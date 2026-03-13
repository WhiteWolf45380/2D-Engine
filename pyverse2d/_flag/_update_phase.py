# ======================================== IMPORTS ========================================
from enum import Enum

# ======================================== FLAG ========================================
class UpdatePhase(Enum):
    """Phase d'actualisation d'un système"""
    EARLY = 0   # Pré-actualisation
    UPDATE = 1  # Actualisation
    LATE = 2    # Post-actualisation