# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...._flag import UpdatePhase
from ....abc import System
from ....math import Vector

from ..._world import World
from ..._component import Transform, RigidBody, Collider

from .._physics import PhysicsSystem

from ._registry import dispatch, Contact
from . import _circle, _rect, _capsule, _polygon, _segment, _ellipse  # noqa: F401

from math import sqrt

# ======================================== CONSTANTES ========================================
_SLOP = 0.5         # pénétration ignorée (px)
_BAUMGARTE = 0.2    # fraction de correction de position par frame
_WARM_BIAS = 0.8    # fraction des impulsions précédentes ré-appliquées au warm start

_MAX_CORRECTION = 8.0           # px/frame pour éviter les sauts à gros dt
_EXTRA_ITER_THRESHOLD = 4.0
_EXTRA_ITER = 4
_MAX_MASS_RATIO = 0.95          # corps léger reçoit au plus 95% de la correction

# ======================================== HELPERS ========================================
def _shape_world_origin(tr: Transform, col: Collider) -> tuple[float, float]:
    """Retourne la position de l'origine locale de la shape dans l'espace monde"""
    ox, oy, bw, bh = col.shape.bounding_box()
    x = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
    y = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]
    return x, y

def _bbox_center_world(tr: Transform, col: Collider) -> tuple[float, float, float, float]:
    """Centre monde du bounding box + demi-dimensions"""
    ox, oy, bw, bh = col.shape.bounding_box()
    wx = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
    wy = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]
    return wx + ox + bw * 0.5, wy + oy + bh * 0.5, bw * 0.5, bh * 0.5

# ======================================== CONTACT CACHE ========================================
class _CachedContact:
    """Impulsions accumulées + normale lissée pour une paire de contacts persistante"""
    __slots__ = ("jn", "jt", "normal")

    def __init__(self):
        self.jn: float = 0.0
        self.jt: float = 0.0
        self.normal: tuple | None = None  # (nx, ny) de la frame précédente


# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions"""
    phase = UpdatePhase.UPDATE
    exclusive = True
    requires = (PhysicsSystem,)

    def __init__(self, broadphase: bool = True, iterations: int = 6):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None
        self._iterations: int = max(1, int(iterations))
        self._cache: dict[tuple[int, int], _CachedContact] = {}     # {(id_a, id_b): _CachedContact}

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
            pairs = [(entities[i], entities[j]) for i in range(n) for j in range(i + 1, n)]

        # Détection + warm start
        active_contacts: list[tuple] = []  # (a, b, contact_lissé, cached)
        active_keys: set[tuple[int, int]] = set()
        max_depth = 0.0

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

            ia, ib = id(a), id(b)
            key = (ia, ib) if ia < ib else (ib, ia)
            active_keys.add(key)

            if key not in self._cache:
                self._cache[key] = _CachedContact()
            cached = self._cache[key]

            nx, ny = contact.normal.x, contact.normal.y
            if cached.normal is not None:
                pnx, pny = cached.normal
                dot = nx * pnx + ny * pny
                if dot > 0.95:
                    mix = 0.7
                    mnx = nx * mix + pnx * (1.0 - mix)
                    mny = ny * mix + pny * (1.0 - mix)
                    n_len = sqrt(mnx * mnx + mny * mny) or 1.0
                    nx, ny = mnx / n_len, mny / n_len
            cached.normal = (nx, ny)
            contact = Contact(type(contact.normal)(nx, ny), contact.depth)

            if contact.depth > max_depth:
                max_depth = contact.depth

            active_contacts.append((a, b, contact, cached))
            self._warm_start(a, b, contact, cached)

        # Purge des contacts disparus
        for key in list(self._cache):
            if key not in active_keys:
                del self._cache[key]

        iterations = self._iterations
        if max_depth > _EXTRA_ITER_THRESHOLD:
            iterations += _EXTRA_ITER

        # Itérations du solveur
        for _ in range(iterations):
            for a, b, contact, cached in active_contacts:
                self._resolve(a, b, contact, cached)

    # ======================================== WARM START ========================================
    def _warm_start(self, a, b, contact: Contact, cached: _CachedContact):
        """Ré-applique une fraction des impulsions de la frame précédente"""
        if not a.has(RigidBody) or not b.has(RigidBody):
            return

        rb_a: RigidBody = a.get(RigidBody)
        rb_b: RigidBody = b.get(RigidBody)
        static_a = rb_a.is_static()
        static_b = rb_b.is_static()
        if static_a and static_b:
            return

        nx, ny = contact.normal.x, contact.normal.y
        tx, ty = -ny, nx

        # Impulsions warm-startées
        jn = cached.jn * _WARM_BIAS
        jt = cached.jt * _WARM_BIAS

        ix = nx * jn + tx * jt
        iy = ny * jn + ty * jt

        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

    # ======================================== DÉTECTION ========================================
    def _detect(self, col_a: Collider, tr_a: Transform, col_b: Collider, tr_b: Transform) -> Contact | None:
        ax, ay = _shape_world_origin(tr_a, col_a)
        bx, by = _shape_world_origin(tr_b, col_b)

        a_cx, a_cy, ahw, ahh = _bbox_center_world(tr_a, col_a)
        b_cx, b_cy, bhw, bhh = _bbox_center_world(tr_b, col_b)
        if abs(a_cx - b_cx) > ahw + bhw or abs(a_cy - b_cy) > ahh + bhh:
            return None
        return dispatch(col_a.shape, ax, ay, col_b.shape, bx, by)

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact, cached: _CachedContact):
        """Solveur d'impulsion avec accumulation (Sequential Impulse Solver)"""
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
        depth  = contact.depth
        nx, ny = normal.x, normal.y
        tx, ty = -ny, nx

        if not has_rb_a or not has_rb_b:
            correction = max(depth - _SLOP, 0.0) * _BAUMGARTE
            if correction > 0:
                if static_a:
                    tr_b.x -= nx * correction
                    tr_b.y -= ny * correction
                else:
                    tr_a.x += nx * correction
                    tr_a.y += ny * correction
            return

        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass
        inv_sum = inv_a + inv_b
        if inv_sum == 0:
            return

        rel_vx = rb_a.velocity.x - rb_b.velocity.x
        rel_vy = rb_a.velocity.y - rb_b.velocity.y
        vel_along = rel_vx * nx + rel_vy * ny

        # Correction de position (Baumgarte)
        if vel_along < 0:
            correction = min(
                max(depth - _SLOP, 0.0) * _BAUMGARTE,
                _MAX_CORRECTION,
            )
            if correction > 0:
                if static_a:
                    tr_b.x -= nx * correction
                    tr_b.y -= ny * correction
                elif static_b:
                    tr_a.x += nx * correction
                    tr_a.y += ny * correction
                else:
                    ra = inv_a / inv_sum
                    rb = inv_b / inv_sum
                    ra = min(ra, _MAX_MASS_RATIO)
                    rb = min(rb, _MAX_MASS_RATIO)
                    tr_a.x += nx * correction * ra
                    tr_a.y += ny * correction * ra
                    tr_b.x -= nx * correction * rb
                    tr_b.y -= ny * correction * rb

        # Impulsion normale avec accumulation
        restitution = min(rb_a.restitution, rb_b.restitution)
        bias = _BAUMGARTE * max(depth - _SLOP, 0.0)
        dv_n = vel_along + bias

        j_delta_n = -dv_n / inv_sum
        if vel_along < -0.5:
            j_delta_n = -(1.0 + restitution) * vel_along / inv_sum

        # Clamp de l'accumulateur : jn ≥ 0
        old_jn = cached.jn
        cached.jn = max(0.0, old_jn + j_delta_n)
        j_delta_n = cached.jn - old_jn

        # Friction tangentielle avec accumulation
        friction = (rb_a.friction + rb_b.friction) * 0.5
        vel_tan = rel_vx * tx + rel_vy * ty
        j_delta_t = -vel_tan / inv_sum

        # Clamp de l'accumulateur : cône de Coulomb |jt| ≤ μ·jn
        old_jt = cached.jt
        max_jt = friction * cached.jn
        cached.jt = max(-max_jt, min(max_jt, old_jt + j_delta_t))
        j_delta_t = cached.jt - old_jt

        # Application des deltas
        ix = nx * j_delta_n + tx * j_delta_t
        iy = ny * j_delta_n + ty * j_delta_t

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

        # Annulation de l'accélération dans la direction du contact
        if not static_a:
            proj = rb_a._acceleration.x * nx + rb_a._acceleration.y * ny
            if proj < 0:
                rb_a._acceleration = Vector(rb_a._acceleration.x - proj * nx, rb_a._acceleration.y - proj * ny)
        if not static_b:
            proj = rb_b._acceleration.x * (-nx) + rb_b._acceleration.y * (-ny)
            if proj < 0:
                rb_b._acceleration = Vector(rb_b._acceleration.x + proj * nx, rb_b._acceleration.y + proj * ny)

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Force une recalibration au prochain update"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()

    def clear_cache(self):
        """Vide le cache d'impulsions (changement de scène, etc.)"""
        self._cache.clear()

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
            _, _, w, h = e.get(Collider).shape.bounding_box()
            hw, hh = w * 0.5, h * 0.5
            if hw > max_extent: max_extent = hw
            if hh > max_extent: max_extent = hh
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
        ox, oy, bw, bh = col.shape.bounding_box()
        cs = self._cell_size

        wx = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
        wy = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]

        if rb is not None and not rb.is_static():
            pwx = rb.prev_x + (-ox - tr.anchor.x * bw) + col.offset[0]
            pwy = rb.prev_y + (-oy - tr.anchor.y * bh) + col.offset[1]
            min_x = min(wx + ox, pwx + ox)
            max_x = max(wx + ox + bw, pwx + ox + bw)
            min_y = min(wy + oy, pwy + oy)
            max_y = max(wy + oy + bh, pwy + oy + bh)
        else:
            min_x = wx + ox
            max_x = wx + ox + bw
            min_y = wy + oy
            max_y = wy + oy + bh

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