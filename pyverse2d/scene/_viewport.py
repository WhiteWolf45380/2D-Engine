# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..math import Point

from numbers import Real

# ======================================== VIEWPORT ========================================
class Viewport:
    """Zone de l'espace logique

    Args:
        origin: position du coin bas gauche du viewport
        width: largeur en pixels logiques (0.0 = tout)
        height: hauteur en pixels logiques (0.0 = tout)
    """
    __slots__ = ("_origin", "_width", "_height")

    def __init__(
        self,
        origin: Point = (0.0, 0.0),
        width: Real = 0.0,
        height: Real = 0.0,
    ):
        self._origin: Point = Point(origin)
        self._width: float = positive(float(expect(width, Real)), arg="width")
        self._height: float = positive(float(expect(height, Real)), arg="height")

    # ======================================== PROPERTIES ========================================
    @property
    def origin(self) -> Point:
        """Position du coin bas gauche

        L'origine peut-être un objet mathématique ``Point`` ou un tuple ``(x, y)``
        """
        return self._origin
    
    @origin.setter
    def origin(self, value: Point):
        self._origin.x = value[0]
        self._origin.y = value[1]

    @property
    def x(self) -> float:
        """Cordonnée horizontale du coin bas gauche
        
        La valeur doit être un ``Réel``.
        """
        return self._origin.x
    
    @x.setter
    def x(self, value: Real):
        self._origin.x = value

    @property
    def y(self) -> float:
        """Coordonnée verticale du coin bas gauche

        La valeur doit être un ``Réel``.
        """
        return self._origin.y
    
    @y.setter
    def y(self, value: Real):
        self._origin.y = value

    @property
    def width(self) -> float:
        """Largeur du viewport
        
        La largeur doit être un ``Réel`` positif non nul.
        """
        return self._width
    
    @width.setter
    def width(self, value: Real):
        self._width = positive(float(expect(value, Real)), arg="width")

    @property
    def height(self) -> float:
        """Hauteur du viewport
        
        La hauteur doit être un ``Réel`` positif non nul.
        """
        return self._height
    
    @height.setter
    def height(self, value: Real):
        self._height = positive(float(expect(value, Real)), arg="height")

    # ======================================== RESOLVING ========================================
    def resolve(self, screen_width: int, screen_height: int) -> tuple[float, float, float, float]:
        """Renvoie ``(x, y, width, height)`` résolus dans l'espace virtuel

        Args:
            virtual_width: largeur de l'espace virtuel
            virtual_height: hauteur de l'espace virtuel
        """
        w = self._width  if self._width != 0.0 else screen_width
        h = self._height if self._height != 0.0 else screen_height
        return (self.x, self.y, w, h)