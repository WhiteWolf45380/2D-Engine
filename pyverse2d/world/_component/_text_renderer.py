# ======================================== IMPORTS ========================================
from ..._internal import expect, clamped
from ...abc import Component
from ...asset import Text
from ...math import Vector

from typing import Iterator
from numbers import Real

# ======================================== COMPONENT ========================================
class TextRenderer(Component):
    """Composant gérant le rendu"""
    __slots__ = ("_text", "_offset", "_opacity", "_z", "_visible")
    requires = ("Transform",)

    def __init__(
            self,
            text: Text = None,
            offset: Vector = (0.0, 0.0),
            opacity: Real = 1.0,
            z: int = 0,
            visible: bool = True,
        ):
        """
        Args:
            text(Text, optional): texte du rendu
            offset(Vector, optional): décalage par rapport au Transform
            opacity(Real, optional): facteur d'opacité de l'image
            z(int, optional): ordre de rendu
            visible(bool, optional): visibilité
        """
        self._text: Text = expect(text, Text)
        self._offset: Vector = Vector(offset)
        self._opacity: float = float(clamped(expect(opacity, Real)))
        self._z: int = expect(z, int)
        self._visible: bool = expect(visible, bool)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"TextRenderer(text={self._text}, opacity={self._opacity}, z={self._z}, visible={self._visible})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Text, Vector, float, int]:
        """Renvoie le composant sous forme de tuple"""
        return (self._text, self._offset, self._opacity, self._z)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._text, self._offset, self._opacity, self._z]
    
    # ======================================== GETTERS ========================================
    @property
    def text(self) -> Text:
        """Renvoie le texte du renderer"""
        return self._text
    
    @property
    def offset(self) -> Vector:
        """Renvoie le décalage par rapport au Transform"""
        return self._offset
    
    @property
    def opacity(self) -> float:
        """Renvoie le facteur d'opacité"""
        return self._opacity
    
    @property
    def z(self) -> int:
        """Renvoie l'ordre de rendu"""
        return self._z
    
    # ======================================== SETTERS ========================================
    @offset.setter
    def offset(self, value: Vector):
        """Fixe le décalage par rapport au Transform"""
        self._offset = Vector(value)

    @opacity.setter
    def opacity(self, value: Real):
        """Fixe le facteur d'opacité"""
        self._opacity = float(clamped(expect(value, Real)))
    
    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible

    # ======================================== PUBLIC METHODS ========================================
    def show(self):
        """Montre le texte"""
        self._visible = True

    def hide(self):
        """Cache le texte"""
        self._visible = False