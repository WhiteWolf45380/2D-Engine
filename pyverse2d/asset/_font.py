# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..abc import Asset

import pyglet
import os
import importlib.resources as resources

from numbers import Real
from pyglet.font.base import Font as PygletFont

# ======================================== OBJET ========================================
class Font(Asset):
    """
    Descripteur de police

    Args:
        font(str): nom ou path de la police
        size(int, optional): taille de la police
    """
    __slots__ = ("_name", "_size", "_glyph_cache", "_pyglet_font", "_initialized")
    _font_cache: dict[tuple[str, int], Font] = {}

    def __new__(cls, name: str = None, size: int=16):
        key = (name, size)
        if key in cls._font_cache:
            return cls._font_cache[key]
        obj = super().__new__(cls)
        cls._font_cache[key] = obj
        return obj

    def __init__(self, name: str = None, size=16):
        # Déjà initialisé
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # Paramètres
        self._size: int = expect(size, int)
        self._glyph_cache: dict[str, Glyph] = {}
        
        # Chargement de la police
        if name and name.lower().endswith((".ttf", ".otf")):
            # Path
            try:
                pyglet.font.add_file(name)
                loaded_font = pyglet.font.load(os.path.splitext(os.path.basename(name))[0], self._size)
                self._name: str = loaded_font.name
                self._pyglet_font: PygletFont = loaded_font
            
            # Fallback
            except Exception:
                self._name: str | None = None
                self._pyglet_font: PygletFont = self._load_default_font()
        
        # SysFont
        elif name:
            loaded_font = pyglet.font.load(name, self._size)
            self._name = loaded_font.name
            self._pyglet_font = loaded_font
        
        # Default Font
        else:
            self._pyglet_font = self._load_default_font()
            self._name = self._pyglet_font.name

        # Initialisation terminée
        self._initialized: bool = True
    
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de la police"""
        return f"Font(name={self._name}, size={self._size})"
    
    # ======================================== GETTERS ========================================
    @property
    def name(self) -> str:
        """Renvoie le nom de la police"""
        return self._name
    
    @property
    def size(self) -> int:
        """Renvoie la taille de la police"""
        return self._size
    
    @property
    def ascent(self) -> int:
        """Renvoie le dépassement haut de la police"""
        return self._pyglet_font.ascent
    
    @property
    def descent(self) -> int:
        """Renvoie le dépassement bas de la police"""
        return self._pyglet_font.descent
    
    @property
    def native(self) -> PygletFont:
        """Renvoie la font pyglet"""
        return self._pyglet_font
    
    @classmethod
    def get_fonts(cls) -> list[str]:
        """Retourne la liste des polices disponibles sur le système"""
        fonts = pyglet.font.get_fonts()
        names = {f.name for f in fonts}
        return sorted(names)

    # ======================================== PUBLIC METHODS ========================================
    def text_width(self, text: str) -> int:
        """
        Renvoie la largeur théorique d'un text

        Args:
            text(str): texte à vérifier
        """
        return sum(self._get_glyph(c).advance for c in text)
    
    def text_height(font: Font, text: str) -> int:
        """
        Renvoie la hauteur théorique d'un texte

        Args:
            text(str): texte à vérifier
        """
        return max(font._get_glyph(c).height for c in text)

    def clip_text(self, text: str, max_width: Real, suffix: str = "") -> str:
        """
        Retourne le texte tronqué pour rentrer dans max_width
        
        Args:
            text(str): text à tronquer
            max_width(Real): largeur maximale du texte (en px)
            suffix(str, optional): suffixe de tronquage
        """
        if not text: return ""
    
        suffix_width = self.text_width(suffix) if suffix else 0
        effective_width = max_width - suffix_width
        if effective_width <= 0:
            return suffix if suffix else ""

        lo = 0
        hi = len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.text_width(text[:mid]) <= effective_width:
                lo = mid
            else:
                hi = mid - 1

        if lo < len(text) and suffix:
            return text[:lo] + suffix
        return text[:lo]

    # ======================================== INTERNALS ========================================
    def _load_default_font(self) -> PygletFont:
        """Charge la police interne par défaut"""
        with resources.path("pyverse2d._assets", "freesansbold.ttf") as path:
            base_name = os.path.splitext(os.path.basename(path))[0]
            font_obj = pyglet.font.load(base_name, self._size)
            self._name = font_obj.name
            return font_obj

    def _get_glyph(self, char: str) -> Glyph:
        """Renvoie un _Glyph"""
        if char not in self._glyph_cache:
            pyglet_glyph = self._pyglet_font.get_glyphs(char)[0]
            self._glyph_cache[char] = Glyph(
                advance=pyglet_glyph.advance,
                width=pyglet_glyph.width,
                height=pyglet_glyph.height,
                tex_coords=getattr(pyglet_glyph, "tex_coords", None)
            )
        return self._glyph_cache[char]

# ======================================== GLYPH OBJECT ========================================
class Glyph:
    """Stocke les informations essentielles d'un glyphe"""
    def __init__(self, advance, width, height, tex_coords=None):
        self.advance = advance
        self.width = width
        self.height = height
        self.tex_coords = tex_coords