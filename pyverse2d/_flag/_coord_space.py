# ======================================== IMPORTS ========================================
from enum import IntEnum

# ======================================== FLAG ========================================
class CoordSpace(IntEnum):
    """Espaces de coordonnées"""
    WORLD = "world"
    FRAMEBUFFER = "framebuffer"
    WINDOW = "window"

# ======================================== EXPORTS ========================================
__all__ = [
    "CoordSpace",
]