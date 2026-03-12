# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import sqrt

from ..ecs import System, World
from ..component import Transform, RigidBody
from ..component._collider import Collider
from ..math import Vector
from ..shape import Circle, Rect, Capsule, Ellipse, Segment, Polygon
from .._phase import Phase

from typing import NamedTuple

# ======================================== SPATIAL HASH ========================================
class _SpatialHash:
    """
    Grille spatiale pour la broadphase de collision.
    La taille des cellules est calculée automatiquement au premier appel.
    """

    def __init__(self):
        self._cell_size: float | None          = None
        self._cells: dict[tuple[int, int], list] = {}

    def clear(self):
        """Vide la grille"""
        self._cells.clear()

    def calibrate(self, entities: list):
        """
        Calcule la taille de cellule optimale depuis les colliders présents.
        Appelé une seule fois au premier update.

        Args:
            entities: entités ayant un Collider et un Transform
        """
        max_extent = 0.0
        for entity in entities:
            hw, hh = self._half_extents(entity.get(Collider).shape)
            max_extent = max(max_extent, hw, hh)
        self._cell_size = max(max_extent * 2.0, 1.0)

    def insert(self, entity, collider: Collider, transform: Transform):
        """
        Insère une entité dans toutes les cellules qu'elle occupe

        Args:
            entity: entité à insérer
            collider(Collider): collider de l'entité
            transform(Transform): transform de l'entité
        """
        x  = transform.x + collider.offset[0]
        y  = transform.y + collider.offset[1]
        hw, hh = self._half_extents(collider.shape)
        cs = self._cell_size

        min_cx = int((x - hw) // cs)
        max_cx = int((x + hw) // cs)
        min_cy = int((y - hh) // cs)
        max_cy = int((y + hh) // cs)

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                key = (cx, cy)
                if key not in self._cells:
                    self._cells[key] = []
                self._cells[key].append(entity)

    def get_pairs(self) -> list[tuple]:
        """
        Renvoie toutes les paires candidates à la collision.
        Chaque paire n'apparaît qu'une seule fois.
        """
        seen:  set[frozenset] = set()
        pairs: list[tuple]    = []

        for cell in self._cells.values():
            n = len(cell)
            for i in range(n):
                for j in range(i + 1, n):
                    key = frozenset((cell[i].id, cell[j].id))
                    if key not in seen:
                        seen.add(key)
                        pairs.append((cell[i], cell[j]))

        return pairs

    def _half_extents(self, shape) -> tuple[float, float]:
        """Renvoie les demi-dimensions de la shape (AABB)"""
        if isinstance(shape, Circle):
            return shape.radius, shape.radius
        if isinstance(shape, Rect):
            return shape.width * 0.5, shape.height * 0.5
        if isinstance(shape, Capsule):
            return shape.radius, shape.height * 0.5
        if isinstance(shape, Ellipse):
            return shape.rx, shape.ry
        if isinstance(shape, Polygon):
            xs = [p.x for p in shape.points]
            ys = [p.y for p in shape.points]
            return (max(xs) - min(xs)) * 0.5, (max(ys) - min(ys)) * 0.5
        if isinstance(shape, Segment):
            dx = abs(shape.B.x - shape.A.x)
            dy = abs(shape.B.y - shape.A.y)
            return dx * 0.5 + shape.width, dy * 0.5 + shape.width
        return 32.0, 32.0

# ======================================== CONTACT ========================================
class Contact(NamedTuple):
    """Résultat d'une détection de collision"""
    normal: Vector
    depth:  float

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """
    Système de détection et résolution des collisions.

    Phase UPDATE — après GravitySystem, avant PhysicsSystem.

    Broadphase via grille spatiale — taille de cellule calculée automatiquement
    depuis les colliders présents au premier update.
    Narrowphase par type de shape.
    Résolution par impulsion + friction tangentielle.

    Args:
        broadphase(bool): active la grille spatiale (désactiver pour debug uniquement)
    """
    phase = Phase.UPDATE

    def __init__(self, broadphase: bool = True):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Détecte et résout les collisions entre toutes les entités

        Args:
            world(World): monde à mettre à jour
            dt(float): delta time
        """
        entities = world.query(Collider, Transform)

        if self._hash is not None:
            # Calibration automatique au premier update
            if self._hash._cell_size is None:
                self._hash.calibrate(entities)

            self._hash.clear()
            for entity in entities:
                col: Collider = entity.get(Collider)
                if col.is_active():
                    self._hash.insert(entity, col, entity.get(Transform))

            pairs = self._hash.get_pairs()
        else:
            # Brute force O(n²) — debug uniquement
            n = len(entities)
            pairs = [(entities[i], entities[j]) for i in range(n) for j in range(i + 1, n)]

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
        """Dispatche vers la bonne fonction de détection selon les shapes"""
        ax = tr_a.x + col_a.offset[0]
        ay = tr_a.y + col_a.offset[1]
        bx = tr_b.x + col_b.offset[0]
        by = tr_b.y + col_b.offset[1]
        sa = col_a.shape
        sb = col_b.shape

        if isinstance(sa, Circle) and isinstance(sb, Circle):
            return self._circle_circle(ax, ay, sa.radius, bx, by, sb.radius)
        if isinstance(sa, Circle) and isinstance(sb, Rect):
            return self._circle_rect(ax, ay, sa.radius, bx, by, sb.width, sb.height)
        if isinstance(sa, Rect) and isinstance(sb, Circle):
            c = self._circle_rect(bx, by, sb.radius, ax, ay, sa.width, sa.height)
            return Contact(-c.normal, c.depth) if c else None
        if isinstance(sa, Rect) and isinstance(sb, Rect):
            return self._rect_rect(ax, ay, sa.width, sa.height, bx, by, sb.width, sb.height)
        if isinstance(sa, Circle) and isinstance(sb, Capsule):
            return self._circle_capsule(ax, ay, sa.radius, bx, by, sb.radius, sb.spine)
        if isinstance(sa, Capsule) and isinstance(sb, Circle):
            c = self._circle_capsule(bx, by, sb.radius, ax, ay, sa.radius, sa.spine)
            return Contact(-c.normal, c.depth) if c else None
        if isinstance(sa, Capsule) and isinstance(sb, Capsule):
            return self._capsule_capsule(ax, ay, sa.radius, sa.spine, bx, by, sb.radius, sb.spine)

        return self._aabb_fallback(sa, ax, ay, sb, bx, by)

    # ======================================== NARROWPHASE ========================================
    def _circle_circle(self, ax, ay, ra, bx, by, rb) -> Contact | None:
        """Cercle vs Cercle"""
        dx      = ax - bx
        dy      = ay - by
        dist_sq = dx * dx + dy * dy
        radii   = ra + rb
        if dist_sq >= radii * radii:
            return None
        dist = sqrt(dist_sq) or 1e-8
        return Contact(Vector(dx / dist, dy / dist), radii - dist)

    def _circle_rect(self, cx, cy, r, rx, ry, rw, rh) -> Contact | None:
        """Cercle vs Rect (AABB)"""
        half_w  = rw * 0.5
        half_h  = rh * 0.5
        rx_c    = rx + half_w
        ry_c    = ry + half_h
        dx      = cx - rx_c
        dy      = cy - ry_c
        near_x  = rx_c + max(-half_w, min(half_w, dx))
        near_y  = ry_c + max(-half_h, min(half_h, dy))
        ddx     = cx - near_x
        ddy     = cy - near_y
        dist_sq = ddx * ddx + ddy * ddy
        if dist_sq >= r * r:
            return None
        dist = sqrt(dist_sq) or 1e-8
        return Contact(Vector(ddx / dist, ddy / dist), r - dist)

    def _rect_rect(self, ax, ay, aw, ah, bx, by, bw, bh) -> Contact | None:
        """Rect vs Rect (AABB)"""
        a_cx      = ax + aw * 0.5
        a_cy      = ay + ah * 0.5
        b_cx      = bx + bw * 0.5
        b_cy      = by + bh * 0.5
        dx        = a_cx - b_cx
        dy        = a_cy - b_cy
        overlap_x = (aw + bw) * 0.5 - abs(dx)
        overlap_y = (ah + bh) * 0.5 - abs(dy)
        if overlap_x <= 0 or overlap_y <= 0:
            return None
        if overlap_x < overlap_y:
            return Contact(Vector(1.0 if dx > 0 else -1.0, 0.0), overlap_x)
        return Contact(Vector(0.0, 1.0 if dy > 0 else -1.0), overlap_y)

    def _circle_capsule(self, cx, cy, cr, capx, capy, cap_r, spine) -> Contact | None:
        """Cercle vs Capsule"""
        closest_y = max(capy, min(capy + spine, cy))
        return self._circle_circle(cx, cy, cr, capx, closest_y, cap_r)

    def _capsule_capsule(self, ax, ay, ar, a_spine, bx, by, br, b_spine) -> Contact | None:
        """Capsule vs Capsule"""
        return self._circle_circle(ax, ay + a_spine * 0.5, ar, bx, by + b_spine * 0.5, br)

    def _aabb_fallback(self, sa, ax, ay, sb, bx, by) -> Contact | None:
        """AABB générique pour les shapes non supportées nativement"""
        def bounds(shape, x, y):
            if isinstance(shape, Ellipse):
                return x - shape.rx, y - shape.ry, shape.rx * 2, shape.ry * 2
            if isinstance(shape, Segment):
                dx = abs(shape.B.x - shape.A.x)
                dy = abs(shape.B.y - shape.A.y)
                return x, y, dx + shape.width * 2, dy + shape.width * 2
            if isinstance(shape, Polygon):
                xs = [p.x for p in shape.points]
                ys = [p.y for p in shape.points]
                return x + min(xs), y + min(ys), max(xs) - min(xs), max(ys) - min(ys)
            return x, y, 1.0, 1.0

        ax2, ay2, aw, ah = bounds(sa, ax, ay)
        bx2, by2, bw, bh = bounds(sb, bx, by)
        return self._rect_rect(ax2, ay2, aw, ah, bx2, by2, bw, bh)

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact):
        """Résout la collision entre deux entités"""
        has_rb_a  = a.has(RigidBody)
        has_rb_b  = b.has(RigidBody)
        rb_a: RigidBody | None = a.get(RigidBody) if has_rb_a else None
        rb_b: RigidBody | None = b.get(RigidBody) if has_rb_b else None
        static_a  = (not has_rb_a) or rb_a.is_static()
        static_b  = (not has_rb_b) or rb_b.is_static()

        if static_a and static_b:
            return

        tr_a: Transform = a.get(Transform)
        tr_b: Transform = b.get(Transform)
        normal = contact.normal
        depth  = contact.depth

        # Correction de position
        if static_a:
            tr_b.x -= normal.x * depth
            tr_b.y -= normal.y * depth
        elif static_b:
            tr_a.x += normal.x * depth
            tr_a.y += normal.y * depth
        else:
            half    = depth * 0.5
            tr_a.x += normal.x * half
            tr_a.y += normal.y * half
            tr_b.x -= normal.x * half
            tr_b.y -= normal.y * half

        if not has_rb_a or not has_rb_b:
            return

        # Impulsion
        rel_vx           = rb_a.velocity.x - rb_b.velocity.x
        rel_vy           = rb_a.velocity.y - rb_b.velocity.y
        vel_along_normal = rel_vx * normal.x + rel_vy * normal.y

        if vel_along_normal > 0:
            return

        restitution  = min(rb_a.restitution, rb_b.restitution)
        inv_mass_a   = 0.0 if static_a else 1.0 / rb_a.mass
        inv_mass_b   = 0.0 if static_b else 1.0 / rb_b.mass
        inv_mass_sum = inv_mass_a + inv_mass_b

        if inv_mass_sum == 0:
            return

        j         = -(1.0 + restitution) * vel_along_normal / inv_mass_sum
        impulse_x = normal.x * j
        impulse_y = normal.y * j

        if not static_a:
            rb_a.velocity = Vector(
                rb_a.velocity.x + impulse_x * inv_mass_a,
                rb_a.velocity.y + impulse_y * inv_mass_a,
            )
        if not static_b:
            rb_b.velocity = Vector(
                rb_b.velocity.x - impulse_x * inv_mass_b,
                rb_b.velocity.y - impulse_y * inv_mass_b,
            )

        # Friction tangentielle
        friction = (rb_a.friction + rb_b.friction) * 0.5
        tan_x    = rel_vx - vel_along_normal * normal.x
        tan_y    = rel_vy - vel_along_normal * normal.y
        t_len    = sqrt(tan_x * tan_x + tan_y * tan_y) or 1e-8
        tan_x   /= t_len
        tan_y   /= t_len
        jt       = -(rel_vx * tan_x + rel_vy * tan_y) / inv_mass_sum
        jt       = max(-abs(j) * friction, min(abs(j) * friction, jt))

        if not static_a:
            rb_a.velocity = Vector(
                rb_a.velocity.x + tan_x * jt * inv_mass_a,
                rb_a.velocity.y + tan_y * jt * inv_mass_a,
            )
        if not static_b:
            rb_b.velocity = Vector(
                rb_b.velocity.x - tan_x * jt * inv_mass_b,
                rb_b.velocity.y - tan_y * jt * inv_mass_b,
            )