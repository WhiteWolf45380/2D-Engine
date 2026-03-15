# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector
from ....shape import Capsule, Polygon, Segment, Circle

from ._registry import (
    Contact, register,
    _closest_pt_on_seg, _closest_pt_seg_to_seg,
    _point_in_convex_poly, _seg_corners,
)
from ._circle import circle_circle

from math import sqrt

# ======================================== HELPER PARTAGÉ ========================================
def _capsule_convex(ax: float, ay: float, spine: float, radius: float, pts: list) -> Contact | None:
    """Capsule vs polygone convexe"""
    n = len(pts)
    min_dist = float("inf")
    mid_x = ax
    mid_y = ay + spine * 0.5
    best_sx, best_sy = mid_x, mid_y
    best_ex, best_ey = pts[0]

    for i in range(n):
        px1, py1 = pts[i]
        px2, py2 = pts[(i + 1) % n]
        edx = px2 - px1
        edy = py2 - py1

        sp_x, sp_y = _closest_pt_seg_to_seg(ax, ay, 0.0, spine, px1, py1, edx, edy)
        ep_x, ep_y = _closest_pt_on_seg(px1, py1, edx, edy, sp_x, sp_y)

        ddx = sp_x - ep_x
        ddy = sp_y - ep_y
        dist = sqrt(ddx * ddx + ddy * ddy)

        if dist < min_dist:
            min_dist = dist
            best_sx, best_sy = sp_x, sp_y
            best_ex, best_ey = ep_x, ep_y

    if min_dist > 1e-6 and _point_in_convex_poly(mid_x, mid_y, pts):
        near_dist = float("inf")
        near_ex, near_ey = pts[0]
        for i in range(n):
            px1, py1 = pts[i]
            px2, py2 = pts[(i + 1) % n]
            ep_x, ep_y = _closest_pt_on_seg(px1, py1, px2 - px1, py2 - py1, mid_x, mid_y)
            ddx = mid_x - ep_x
            ddy = mid_y - ep_y
            d = sqrt(ddx * ddx + ddy * ddy)
            if d < near_dist:
                near_dist = d
                near_ex, near_ey = ep_x, ep_y
        ddx = mid_x - near_ex
        ddy = mid_y - near_ey
        d = sqrt(ddx * ddx + ddy * ddy) or 1e-8
        return Contact(Vector(ddx / d, ddy / d), radius + near_dist)

    if min_dist >= radius:
        return None

    depth = radius - min_dist
    ddx = best_sx - best_ex
    ddy = best_sy - best_ey
    dist = sqrt(ddx * ddx + ddy * ddy)
    if dist < 1e-8:
        cent_x = sum(p[0] for p in pts) / n
        cent_y = sum(p[1] for p in pts) / n
        ddx = mid_x - cent_x
        ddy = mid_y - cent_y
        dist = sqrt(ddx * ddx + ddy * ddy) or 1e-8
    return Contact(Vector(ddx / dist, ddy / dist), depth)

# ======================================== Capsule × Capsule ========================================
@register(Capsule, Capsule)
def capsule_capsule(sa: Capsule, ax, ay, sb: Capsule, bx, by) -> Contact | None:
    """Capsule vs Capsule"""
    px, py = _closest_pt_seg_to_seg(ax, ay, 0.0, sa.spine, bx, by, 0.0, sb.spine)
    qx, qy = _closest_pt_on_seg(bx, by, 0.0, sb.spine, px, py)
    return circle_circle(Circle(sa.radius), px, py, Circle(sb.radius), qx, qy)

# ======================================== Capsule × Polygon ========================================
@register(Capsule, Polygon)
def capsule_polygon(sa: Capsule, ax, ay, sb: Polygon, bx, by) -> Contact | None:
    """Capsule vs Polygone"""
    pts = [(bx + p.x, by + p.y) for p in sb.points]
    return _capsule_convex(ax, ay, sa.spine, sa.radius, pts)