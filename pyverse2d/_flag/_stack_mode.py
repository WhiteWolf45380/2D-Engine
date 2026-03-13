# ======================================== IMPORTS ========================================
from enum import Enum

# ======================================== FLAG ========================================
class StackMode(Enum):
    """Gestion des autres scenes"""
    PAUSE = "pause"         # scene du dessous stop tout
    SUSPEND = "suspend"     # scene du dessous stop update mais continue draw
    OVERLAY = "overlay"     # scene du dessous continue tout