# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....shape import Polygon, Segment

from ._registry import register, Contact, _sat, _seg_corners

# ======================================== Polygon × Polygon ========================================
@register(Polygon, Polygon)
def polygon_polygon(sa: Polygon, ax, ay, sb: Polygon, bx, by) -> Contact | None:
    """Polygone vs Polygone"""
    return _sat(
        [(ax + p.x, ay + p.y) for p in sa.points],
        [(bx + p.x, by + p.y) for p in sb.points],
    )

# ======================================== Polygon × Segment ========================================
@register(Polygon, Segment)
def polygon_segment(sa: Polygon, ax, ay, sb: Segment, bx, by) -> Contact | None:
    """Polygone vs Segment — SAT complet"""
    return _sat(
        [(ax + p.x, ay + p.y) for p in sa.points],
        _seg_corners(bx, by, sb),
    )