# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector
from ....shape import Circle, Rect, Capsule, Ellipse, Segment, Polygon

from ._registry import (
    Contact, register,
    _circle_pts, _closest_pt_on_seg, _closest_pt_on_ellipse
)

from math import sqrt

# ======================================== Circle × Circle ========================================
@register(Circle, Circle)
def circle_circle(sa: Circle, ax, ay, sb: Circle, bx, by) -> Contact | None:
    """Cercle vs Cercle"""
    dx = ax - bx
    dy = ay - by
    dist_sq = dx * dx + dy * dy
    radii = sa.radius + sb.radius
    if dist_sq >= radii * radii:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector(dx / dist, dy / dist), radii - dist)

# ======================================== Circle × Rect ========================================
@register(Circle, Rect)
def circle_rect(sa: Circle, cx, cy, sb: Rect, rx, ry) -> Contact | None:
    """Cercle vs Rect"""
    half_w = sb.width * 0.5
    half_h = sb.height * 0.5
    rc_x = rx + half_w
    rc_y = ry + half_h
    dx = cx - rc_x
    dy = cy - rc_y
    near_x = rc_x + max(-half_w, min(half_w, dx))
    near_y = rc_y + max(-half_h, min(half_h, dy))
    ddx = cx - near_x
    ddy = cy - near_y
    dist_sq = ddx * ddx + ddy * ddy
    if dist_sq >= sa.radius * sa.radius:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector(ddx / dist, ddy / dist), sa.radius - dist)


# ======================================== Circle × Capsule ========================================
@register(Circle, Capsule)
def circle_capsule(sa: Circle, cx, cy, sb: Capsule, capx, capy) -> Contact | None:
    """Cercle vs Capsule"""
    closest_x = capx
    closest_y = max(capy, min(capy + sb.spine, cy))
    return circle_circle(sa, cx, cy, Circle(sb.radius), closest_x, closest_y)


# ======================================== Circle × Polygon ========================================
@register(Circle, Polygon)
def circle_polygon(sa: Circle, cx, cy, sb: Polygon, px, py) -> Contact | None:
    """Cerlce vs Polygone"""
    return _circle_pts(cx, cy, sa.radius, [(px + p.x, py + p.y) for p in sb.points])

# ======================================== Circle × Ellipse ========================================
@register(Circle, Ellipse)
def circle_ellipse(sa: Circle, cx, cy, sb: Ellipse, ex, ey) -> Contact | None:
    """Cercle vs Ellipse"""
    lx = (cx - ex) / sb.rx
    ly = (cy - ey) / sb.ry
    inside = lx * lx + ly * ly <= 1.0

    qx, qy = _closest_pt_on_ellipse(ex, ey, sb.rx, sb.ry, cx, cy)
    dx = cx - qx
    dy = cy - qy
    dist = sqrt(dx * dx + dy * dy) or 1e-8

    if inside:
        return Contact(Vector(dx / dist, dy / dist), sa.radius + dist)
    if dist >= sa.radius:
        return None
    return Contact(Vector(dx / dist, dy / dist), sa.radius - dist)


# ======================================== Circle × Segment ========================================
@register(Circle, Segment)
def circle_segment(sa: Circle, cx, cy, sb: Segment, sx, sy) -> Contact | None:
    """Cerlce vs Segment"""
    ax2 = sx + sb.A.x
    ay2 = sy + sb.A.y
    bx2 = sx + sb.B.x
    by2 = sy + sb.B.y
    dx, dy = bx2 - ax2, by2 - ay2
    cpx, cpy = _closest_pt_on_seg(ax2, ay2, dx, dy, cx, cy)
    half_w = sb.width * 0.5
    total_r = sa.radius + half_w
    ddx, ddy = cx - cpx, cy - cpy
    dist_sq = ddx * ddx + ddy * ddy
    if dist_sq >= total_r * total_r:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector(ddx / dist, ddy / dist), total_r - dist)