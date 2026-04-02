# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..asset import Color
from ..math import Point

from numbers import Real

# ======================================== VIEWPORT ========================================
class Viewport:
    """
    Zone de l'espace virtuel où la caméra s'affiche

    Args:
        origin(Point): position ``(x, y)`` du coin supérieur gauche du viewport
        width (Real): ``largeur`` dans l'espace virtuel (0.0 = tout)
        height (Real): ``hauteur`` dans l'espace virtuel (0.0 = tout)
        border_width(int): ``épaisseur`` de la bordure
        border_color(Color): ``couleur`` de la bordure
    """
    __slots__ = ("_origin", "_width", "_height", "_border", "_border_width", "_border_color")

    def __init__(
        self,
        origin: Point = (0, 0),
        width: Real = 0.0,
        height: Real = 0.0,
        border_width: int = 0,
        border_color: Color = (0, 0, 0, 1.0),
    ):
        self._origin: Point = Point(origin)
        self._width: float = float(positive(expect(width, Real)))
        self._height: float = float(positive(expect(height, Real)))
        self._border_width: int = expect(border_width, int)
        self._border_color: Color = Color(border_color)

    # ======================================== GETTERS ========================================
    @property
    def origin(self) -> Point:
        """Renvoie la position (x, y)"""
        return self._origin

    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._origin.x

    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._origin.y

    @property
    def width(self) -> float:
        """Renvoie la largeur"""
        return self._width

    @property
    def height(self) -> float:
        """Renvoie la hauteur"""
        return self._height

    @property
    def border_width(self) -> int:
        """Renvoie l'épaisseur de la bordure"""
        return self._border_width
    
    @property
    def border_color(self) -> Color:
        """Renvoie la couleur de la bordure"""
        return self._border_color

    # ======================================== SETTERS ========================================
    @origin.setter
    def origin(self, value: Point):
        """Fixe la position (x, y)"""
        self._origin = Point(value)

    @x.setter
    def x(self, value: Real):
        """Fixe la coordonnée horizontale du viewport"""
        self._origin.x = value

    @y.setter
    def y(self, value: Real):
        """Fixe la coordonnée verticale du viewport"""
        self._origin.y = value

    @width.setter
    def width(self, value: Real):
        """Fixe la largeur du viewport"""
        self._width = float(positive(expect(value, Real)))

    @height.setter
    def height(self, value: Real):
        """Fixe la hauteur du viewport"""
        self._height = float(positive(expect(value, Real)))

    @border_width.setter
    def border_width(self, value: Real):
        """Fixe l'épaisseur de la bordure"""
        self._border_width = expect(value, int)

    @border_color.setter
    def border_color(self, value: Color):
        """Fixe la couleur de la bordure"""
        self._border_color = Color(value)

    # ======================================== RÉSOLUTION ========================================
    def resolve(self, virtual_width: int, virtual_height: int) -> tuple[float, float, float, float]:
        """
        Renvoie (x, y, width, height) résolus dans l'espace virtuel

        Args:
            virtual_width (int): largeur de l'espace virtuel
            virtual_height (int): hauteur de l'espace virtuel
        """
        w = self._width  if self._width != 0.0 else virtual_width
        h = self._height if self._height != 0.0 else virtual_height
        return (self.x, self.y, w, h)