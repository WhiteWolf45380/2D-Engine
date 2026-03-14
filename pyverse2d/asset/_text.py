# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..abc import Asset

from ._font import Font

from numbers import Real

# ======================================== OBJET ========================================
class Text(Asset):
    """
    Descripteur de texte

    Args:
        text(str): contenu du texte
        font(Font, optional): police à utiliser
    """
    __slots__ = ("_original_text", "_text", "_font")

    def __init__(self, text: str, font: Font = None):
        self._original_text: str = expect(text, str)
        self._text: str = self._original_text
        self._font: Font = expect(font, Font) if font is not None else Font()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"Text(text={self._text}, font={self._font})"

    # ======================================== GETTERS ========================================
    @property
    def text(self) -> str:
        """Renvoie le contenu du texte"""
        return self._text

    @property
    def font(self) -> Font:
        """Renvoie la police"""
        return self._font

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Text:
        """Renvoie une copie du texte"""
        t = Text(self._original_text, self._font)
        t.text = self._text
        return t

    def copy(self) -> Text:
        """Renvoie une copie du texte"""
        return self.__copy__()

    def with_text(self, text: str) -> Text:
        """
        Renvoie un nouveau Text avec un contenu différent

        Args:
            text(str): nouveau texte
        """
        return Text(expect(text, str), self._font)
 
    def with_font(self, font: Font) -> Text:
        """
        Renvoie un nouveau Text avec une police différente

        Args:
            font(Font): nouvelle font
        """
        return Text(self._original_text, expect(font, Font))
    
    def clip(self, width: Real = 0.0, suffix: str = ""):
        """
        Limite le texte à une certaine largeur

        Args:
            width(Real): largeur maximale (0.0 pour largeur illimitée)
        """
        self._text = self._font.clip_text(self._original_text, max_width=width, suffix=suffix)
    
    def reset_clip(self):
        """Rétablit le texte original."""
        self._text = self._original_text