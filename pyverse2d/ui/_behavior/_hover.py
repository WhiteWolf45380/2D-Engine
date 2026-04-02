# ======================================== IMPORTS ========================================
from ..._rendering import Pipeline, RenderContext
from ...abc import Behavior

from pyverse2d import inputs, ui_manager

# ======================================== BEHAVIOR ========================================
class HoverBehavior(Behavior):
    """Behavior gérant le survol"""
    __slots__ = ("_hovered",)
    _ID: str = "hover"

    def __init__(self):
        # Initialisation du comportement
        super().__init__()

        # Etat
        self._hovered: bool = False

    # ======================================== PROPERTIES ========================================

    # ======================================== PREDICATES ========================================
    def is_hovered(self) -> bool:
        """Indique si le widget est survolé"""
        return self._hovered

    # ======================================== HOOKS ========================================
    def _attach(self, widget) -> None:
        """Hook d'attachement"""
        pass

    def _detach(self) -> None:
        """Hook de détachement"""
        pass

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        pass

    def draw(self, pipeline: Pipeline, context: RenderContext) -> None:
        """Affichage"""
        pass