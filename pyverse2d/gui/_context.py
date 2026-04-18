# ======================================== IMPORTS ========================================
from ..math import Point
from .._rendering import Pipeline

from dataclasses import dataclass
from pyglet.graphics import Group

# ======================================== RENDER CONTEXT ========================================
@dataclass(slots=True)
class RenderContext:
    """Contexte de rendu des widgets"""
    pipeline: Pipeline      # pipeline de rendu
    z: int                  # z-order global
    origin: Point           # ancre globale
    opacity: float          # opacité cumulée
    group: Group            # groupe courant