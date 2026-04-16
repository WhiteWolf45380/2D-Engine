# ======================================== IMPORTS ========================================
from ..math import Point
from ..abc._gui._widget import WidgetGroup

from dataclasses import dataclass

# ======================================== RENDER CONTEXT ========================================
@dataclass(slots=True)
class RenderContext:
    """Contexte de rendu des widgets"""
    z: int                  # z-order global
    origin: Point           # ancre globale
    opacity: float          # opacité cumulée
    group: WidgetGroup      # groupe courant