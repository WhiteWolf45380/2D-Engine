# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, positive, not_null
from ...abc import Component
from ...math import Point, Vector

from typing import Iterator
from numbers import Real

# ======================================== COMPONENT ========================================
class Transform(Component):
    """Composant gérant le positionnement"""
    __slots__ = ("_pos", "_anchor", "_rotation", "_scale")

    def __init__(
            self,
            pos: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            rotation: float = 0.0,
            scale: float = 1.0,
        ):
        """
        Args:
            pos(Point): position
            anchor(Point, optional): ancre de positionnement (écart normalisé à l'origine)
            rotation(float, optional): angle de rotation en radians
            scale(float, otional): facteur de redimensionnement
        """
        self._pos: Point = Point(pos)
        self._anchor: Point = Point(anchor)
        self._rotation: float = float(expect(rotation, Real))
        self._scale: float = float(not_null(positive(expect(scale, Real))))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Transform(x={self._pos.x}, y={self._pos.x}, anchor={self._anchor}, rotation={self._rotation}, scale={self._scale})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Point, Point, float, float]:
        """Renvoie le composant sous forme tuple"""
        return (self._pos, self._anchor, self._rotation, self._scale)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._pos, self._anchor, self._rotation, self._scale]

    # ======================================== GETTERS ========================================
    @property
    def x(self) -> float:
        """Renvoie la coordonnée horizontale"""
        return self._pos.x
    
    @property
    def y(self) -> float:
        """Renvoie la coordonnée verticale"""
        return self._pos.y
    
    @property
    def pos(self) -> Point:
        """Renvoie le point de position"""
        return self._pos
    
    @property
    def anchor(self) -> Point:
        """Renvoie l'ancre de positionnement"""
        return self._anchor
    
    @property
    def rotation(self) -> float:
        """Renvoie la rotation en radians"""
        return self._rotation
    
    @property
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale

    # ======================================== SETTERS ========================================
    @x.setter
    def x(self, value: Real):
        """Fixe la coordonnée horizontale"""
        self._pos.x = float(expect(value, Real))
    
    @y.setter
    def y(self, value: Real):
        """Fixe la coordonnée verticale"""
        self._pos.y = float(expect(value, Real))

    @pos.setter
    def pos(self, value: Point):
        """Fixe le point de posiiton"""
        self._pos = Point(value)

    @anchor.setter
    def anchor(self, value: Point):
        """Fixe l'ancre de positionnement"""
        self._anchor = Point(value)
    
    @rotation.setter
    def rotation(self, value: Real):
        """Fixe la rotation"""
        self._rotation = float(expect(value, Real))
    
    @scale.setter
    def scale(self, value: Real):
        """Fixe le facteur de redimensionnement"""
        self._scale = float(not_null(positive(expect(value, Real))))

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Transform:
        """Renvoie une copie du composant"""
        return Transform(self._pos.copy(), self._anchor, self._rotation, self._scale)
    
    def translate(self, vector: Vector):
        """
        Applique une translation au transform

        Args:
            vector(Vector): vecteur de translation
        """
        self._pos += expect(vector, Vector)