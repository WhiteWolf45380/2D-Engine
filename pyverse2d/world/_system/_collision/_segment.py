# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....shape import Segment

from ._registry import register, Contact, _sat, _seg_corners

# ======================================== Segment × Segment ========================================
@register(Segment, Segment)
def segment_segment(sa: Segment, ax, ay, sb: Segment, bx, by) -> Contact | None:
    """Segment vs Segment"""
    return _sat(_seg_corners(ax, ay, sa), _seg_corners(bx, by, sb))