# ======================================== IMPORTS ========================================
from ...abc import Behavior, Request
from ...math import Point

from pyverse2d import inputs, ui

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

    def on_enter(self) -> None:
        """Au moment du survol"""
        pass

    def when_hovered(self) -> Request:
        """Durant le survol"""
        pass

    def on_leave(self) -> None:
        """Au moment de la fin du survol"""
        pass

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        # Détection du survol
        if ui.hovered is None and self._collides(inputs.relative_mouse_position):
            hovered = ui.ask_hover(self._owner)
        else:
            hovered = False

        # Hooks de changement d'état
        if hovered:
            if not self._hovered:
                self.on_enter()
            self.when_hovered()
        elif not hovered and self._hovered:
            self.on_leave()
        self._hovered = hovered

    # ======================================== HELPERS ========================================
    def _collides(self, point: Point) -> bool:
        """Vérifie si un point est dans le widget"""
        return self._owner.collidespoint(point)