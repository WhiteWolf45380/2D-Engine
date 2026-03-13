# ======================================== IMPORTS ========================================
from enum import Enum

# ======================================== FLAG ========================================
class CameraMode(Enum):
    """Mode de suivi de la caméra appliqué à un Layer"""
    WORLD = 0   # position + zoom
    ZOOM = 1    # zoom uniquement, position ignorée
    SCREEN = 2  # ni position ni zoom