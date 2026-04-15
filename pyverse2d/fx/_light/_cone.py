# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import LightSource
from ...math import Point
from ...math.easing import EasingFunc
from ...asset import Color

from numbers import Real

# ======================================== IMPORTS ========================================
class ConeLight(LightSource):
    """Source de lumière: Point
    
    Args:
        position: position du point
        color: couleur de la lumière émise
        intensity: intensité lumineuse
        falloff: fonction d'atténuation
        enable: activation initiale de la lumière
    """
    __slots__ = (
    )

    def __init__(
            self,
            position: Point = (0.0, 0.0),
            color: Color = (255, 255, 255),
            intensity: Real = 1.0,
            falloff: EasingFunc = None,
            enabled: bool = True,
        ):
        # Initialisation de la source de lumière
        super().__init__(position, color, intensity, falloff, enabled)