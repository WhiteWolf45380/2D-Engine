# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...._flag import UpdatePhase
from ....abc import System
from ....math import Vector

from ..._world import World
from ..._component import Transform, RigidBody, Collider

from .._physics import PhysicsSystem

from ._registry import dispatch, _half_extents, Contact
from . import _circle, _rect, _capsule, _polygon, _segment, _ellipse  # noqa: F401

from math import sqrt

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions"""
    phase = UpdatePhase.UPDATE
    exclusive = True
    requires = (PhysicsSystem,)

    def __init__(self, broadphase: bool = True, iterations: int = 3):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None
        self._iterations: int = max(1, int(iterations))

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        entities = world.query(Collider, Transform)

        if self._hash is not None:
            if self._hash._cell_size is None:
                self._hash.calibrate(entities)
            self._hash.update_dynamic(entities)
            pairs = self._hash.get_pairs()
        else:
            n = len(entities)
            pairs = [
                (entities[i], entities[j])
                for i in range(n)
                for j in range(i + 1, n)
            ]

        for _ in range(self._iterations):
            for a, b in pairs:
                col_a: Collider = a.get(Collider)
                col_b: Collider = b.get(Collider)

                if not col_a.is_active() or not col_b.is_active():
                    continue
                if not col_a.collides_with(col_b):
                    continue

                contact = self._detect(col_a, a.get(Transform), col_b, b.get(Transform))
                if contact is None:
                    continue
                if col_a.is_trigger() or col_b.is_trigger():
                    continue

                self._resolve(a, b, contact)

    # ======================================== DÉTECTION ========================================
    def _detect(self, col_a: Collider, tr_a: Transform, col_b: Collider, tr_b: Transform) -> Contact | None:
        ax = tr_a.x + col_a.offset[0]
        ay = tr_a.y + col_a.offset[1]
        bx = tr_b.x + col_b.offset[0]
        by = tr_b.y + col_b.offset[1]
        sa = col_a.shape
        sb = col_b.shape

        # Pre-reject AABB
        ahw, ahh = _half_extents(sa)
        bhw, bhh = _half_extents(sb)
        if abs(ax - bx) > ahw + bhw or abs(ay - by) > ahh + bhh:
            return None

        return dispatch(sa, ax, ay, sb, bx, by)

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact):
        """Correction de position, impulsion, friction tangentielle"""
        has_rb_a = a.has(RigidBody)
        has_rb_b = b.has(RigidBody)
        rb_a: RigidBody | None = a.get(RigidBody) if has_rb_a else None
        rb_b: RigidBody | None = b.get(RigidBody) if has_rb_b else None
        static_a = (not has_rb_a) or rb_a.is_static()
        static_b = (not has_rb_b) or rb_b.is_static()

        if static_a and static_b:
            return

        if has_rb_a and rb_a.is_sleeping():
            rb_a.wake()
        if has_rb_b and rb_b.is_sleeping():
            rb_b.wake()

        tr_a: Transform = a.get(Transform)
        tr_b: Transform = b.get(Transform)
        normal = contact.normal
        depth = contact.depth

        # ---- Correction de position ----
        if static_a:
            tr_b.x -= normal.x * depth
            tr_b.y -= normal.y * depth
        elif static_b:
            tr_a.x += normal.x * depth
            tr_a.y += normal.y * depth
        else:
            inv_a = 1.0 / rb_a.mass
            inv_b = 1.0 / rb_b.mass
            inv_sum = inv_a + inv_b
            if inv_sum > 0:
                ra = inv_a / inv_sum
                rb = inv_b / inv_sum
                tr_a.x += normal.x * depth * ra
                tr_a.y += normal.y * depth * ra
                tr_b.x -= normal.x * depth * rb
                tr_b.y -= normal.y * depth * rb

        if not has_rb_a or not has_rb_b:
            return

        rel_vx = rb_a.velocity.x - rb_b.velocity.x
        rel_vy = rb_a.velocity.y - rb_b.velocity.y
        vel_along = rel_vx * normal.x + rel_vy * normal.y

        if vel_along > 0:
            return

        restitution = min(rb_a.restitution, rb_b.restitution)
        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass
        inv_sum = inv_a + inv_b

        if inv_sum == 0:
            return

        # ---- Impulsion normale ----
        j = -(1.0 + restitution) * vel_along / inv_sum
        ix = normal.x * j
        iy = normal.y * j

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

        # ---- Friction tangentielle ----
        friction = (rb_a.friction + rb_b.friction) * 0.5
        tx = rel_vx - vel_along * normal.x
        ty = rel_vy - vel_along * normal.y
        t_len = sqrt(tx * tx + ty * ty) or 1e-8
        tx /= t_len
        ty /= t_len
        jt = -(rel_vx * tx + rel_vy * ty) / inv_sum
        jt = max(-abs(j) * friction, min(abs(j) * friction, jt))

        if not static_a:
            rb_a.velocity = Vector(
                rb_a.velocity.x + tx * jt * inv_a,
                rb_a.velocity.y + ty * jt * inv_a,
            )
        if not static_b:
            rb_b.velocity = Vector(
                rb_b.velocity.x - tx * jt * inv_b,
                rb_b.velocity.y - ty * jt * inv_b,
            )

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Force une recalibration au prochain update"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()


# ======================================== SPATIAL HASH ========================================
class _SpatialHash:
    """Grille spatiale broadphase"""

    def __init__(self):
        self._cell_size: float | None = None
        self._dynamic_cells: dict[tuple[int, int], list] = {}
        self._static_cells: dict[tuple[int, int], list] = {}
        self._static_built: bool = False

    def clear_static(self):
        self._static_cells.clear()
        self._static_built = False

    def calibrate(self, entities: list):
        max_extent = 0.0
        for e in entities:
            hw, hh = _half_extents(e.get(Collider).shape)
            if hw > max_extent:
                max_extent = hw
            if hh > max_extent:
                max_extent = hh
        self._cell_size = max(max_extent * 2.0, 1.0)

    def update_dynamic(self, entities: list):
        self._dynamic_cells.clear()
        rebuild = not self._static_built
        for entity in entities:
            col: Collider = entity.get(Collider)
            if not col.is_active():
                continue
            rb = entity.get(RigidBody) if entity.has(RigidBody) else None
            is_static = (rb is None) or rb.is_static()
            if is_static:
                if rebuild:
                    self._insert(self._static_cells, entity, col, entity.get(Transform), None)
            else:
                self._insert(self._dynamic_cells, entity, col, entity.get(Transform), rb)
        if rebuild:
            self._static_built = True

    def _insert(self, cells, entity, col: Collider, tr: Transform, rb):
        x = tr.x + col.offset[0]
        y = tr.y + col.offset[1]
        hw, hh = _half_extents(col.shape)
        cs = self._cell_size
        if rb is not None and not rb.is_static():
            px = rb.prev_x + col.offset[0]
            py = rb.prev_y + col.offset[1]
            min_x, max_x = min(x, px) - hw, max(x, px) + hw
            min_y, max_y = min(y, py) - hh, max(y, py) + hh
        else:
            min_x, max_x = x - hw, x + hw
            min_y, max_y = y - hh, y + hh

        for cx in range(int(min_x // cs), int(max_x // cs) + 1):
            for cy in range(int(min_y // cs), int(max_y // cs) + 1):
                key = (cx, cy)
                if key not in cells:
                    cells[key] = []
                cells[key].append(entity)

    def get_pairs(self) -> list[tuple]:
        seen: set[tuple[int, int]] = set()
        pairs: list[tuple] = []

        for cell in self._dynamic_cells.values():
            n = len(cell)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = cell[i], cell[j]
                    ia, ib = id(a), id(b)
                    key = (ia, ib) if ia < ib else (ib, ia)
                    if key not in seen:
                        seen.add(key)
                        pairs.append((a, b))

        for ck, dyn in self._dynamic_cells.items():
            stat = self._static_cells.get(ck)
            if not stat:
                continue
            for d in dyn:
                for s in stat:
                    id_d, id_s = id(d), id(s)
                    key = (id_d, id_s) if id_d < id_s else (id_s, id_d)
                    if key not in seen:
                        seen.add(key)
                        pairs.append((d, s))
        return pairs