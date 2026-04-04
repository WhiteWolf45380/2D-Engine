# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Manager
from ..math import Point

from ._context import ContextManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering import Window

# ======================================== MANAGER ========================================
class MouseManager(Manager):
    """Gestionnaire de la souris"""
    __slots__ = (
        "_viewport_origin",
        "_mouse_x", "_mouse_y",
        "_mouse_out",
        "_mouse_dx", "_mouse_dy",
        "_drag_dx", "_drag_dy",
        "_scroll_dx", "_scroll_dy",
    )

    def __init__(self, context_manager: ContextManager):
        # Initialisation du gestionnaire
        super().__init__(context_manager)

        # Position
        self._viewport_origin: Point = Point(0, 0)
        self._mouse_x: float = 0.0
        self._mouse_y: float = 0.0
        self._mouse_out: bool = False

        # Deltas
        self._mouse_dx: float = 0.0
        self._mouse_dy: float = 0.0
        self._drag_dx: float = 0.0
        self._drag_dy: float = 0.0
        self._scroll_dx: float = 0.0
        self._scroll_dy: float = 0.0

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> tuple[float, float]:
        """Position absolue de la souris"""
        return self._mouse_x, self._mouse_y

    @property
    def x(self) -> float:
        """Position X absolue de la souris"""
        return self._mouse_x

    @property
    def y(self) -> float:
        """Position Y absolue de la souris"""
        return self._mouse_y

    @property
    def viewport_origin(self) -> Point:
        """Origine du viewport courant"""
        return self._viewport_origin
    
    @property
    def viewport_position(self) -> tuple[float, float]:
        """Position de la souris dans le viewport courant"""
        return self.viewport_x, self.viewport_y

    @property
    def viewport_x(self) -> float:
        """Position X de la souris dans le viewport courant"""
        return self._mouse_x - self._viewport_origin.x

    @property
    def viewport_y(self) -> float:
        """Position Y de la souris dans le viewport courant"""
        return self._mouse_y - self._viewport_origin.y
    
    @property
    def motion(self) -> tuple[float, float]:
        """Déplacement de la souris"""
        return self._mouse_dx, self._mouse_dy

    @property
    def dx(self) -> float:
        """Déplacement horizontal de la souris"""
        return self._mouse_dx

    @property
    def dy(self) -> float:
        """Déplacement vertical de la souris"""
        return self._mouse_dy
    
    @property
    def drag(self) -> tuple[float, float]:
        """Glissement lors du maintien"""
        return self._drag_dx, self.drag_dy

    @property
    def drag_dx(self) -> float:
        """Glissement horizontal lors d'un maintien"""
        return self._drag_dx

    @property
    def drag_dy(self) -> float:
        """Glissement vertical lors d'un maintien"""
        return self._drag_dy
    
    @property
    def scroll(self) -> tuple[float, float]:
        """Défilement de la molette cette frame"""
        return self._scroll_dx, self._scroll_dy

    @property
    def scroll_x(self) -> float:
        """Défilement horizontal de la molette cette frame"""
        return self._scroll_dx

    @property
    def scroll_y(self) -> float:
        """Défilement vertical de la molette cette frame"""
        return self._scroll_dy

    # ======================================== STATE ========================================
    def is_out(self) -> bool:
        """Vérifie si la souris est hors du viewport"""
        return self._mouse_out

    def set_viewport_origin(self, point: Point) -> None:
        """Définit l'origine du viewport courant

        Args:
            point: origine du viewport
        """
        self._viewport_origin = Point(point)

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        pass

    def flush(self) -> None:
        """Nettoyage"""
        self._mouse_dx = 0.0
        self._mouse_dy = 0.0
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._scroll_dx = 0.0
        self._scroll_dy = 0.0

    # ======================================== HANDLERS ========================================
    def _on_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        """Déplacement de la souris"""
        self._compute_position(x, y)
        self._mouse_dx = dx * self._window.width / self._window.screen.width
        self._mouse_dy = dy * self._window.height / self._window.screen.height

    def _on_drag(self, x: float, y: float, dx: float, dy: float, buttons: int) -> None:
        """Glissement lors du maintien"""
        self._compute_position(x, y)
        self._drag_dx = dx * self._window.width / self._window.screen.width
        self._drag_dy = dy * self._window.height / self._window.screen.height

    def _on_press(self, x: float, y: float, button: int) -> None:
        """Pression d'un bouton"""
        self._compute_position(x, y)

    def _on_release(self, x: float, y: float, button: int) -> None:
        """Relachement d'un bouton"""
        self._compute_position(x, y)

    def _on_enter(self, x: float, y: float) -> None:
        """Entrée dans la fenêtre"""
        self._mouse_out = False
        self._compute_position(x, y)

    def _on_leave(self, x: float, y: float) -> None:
        """Sortie de la fenêtre"""
        self._mouse_out = True
        self._compute_position(x, y)

    def _on_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> None:
        """Défilement de la molette"""
        self._scroll_dx = scroll_x
        self._scroll_dy = scroll_y

    # ======================================== INTERNALS ========================================
    def _compute_position(self, x: float, y: float) -> None:
        """Convertit les coords pyglet en coords écran centrées"""
        lx, ly = self._window.window_to_screen(x, y)
        self._mouse_x = lx - self._window.screen.half_width
        self._mouse_y = ly - self._window.screen.half_height
        hw, hh = self._window.screen.half_width, self._window.screen.half_height
        self._mouse_out = not (-hw <= self._mouse_x <= hw and -hh <= self._mouse_y <= hh)