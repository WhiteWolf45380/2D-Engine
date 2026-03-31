# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped
from ..._rendering import Pipeline, RenderContext, PygletLabelRenderer
from ...asset import Text, Color
from ...abc import Widget
from ...math import Point

from numbers import Real
from typing import Literal

# ======================================== CONSTANTS ========================================
HorizontalAlign = Literal["left", "center", "right"]

# ======================================== WIDGET ========================================
class Label(Widget):
    """
    Composant UI simple: Label

    Args:
        text(Text): texte à rendre
        position(Point, Point): position
        anchor(Point, optional): ancre relative locale
        rotation(Real, optional): rotation en degrés
        weight(str, optional): graisse ('bold', 'thin', '100'…'900', ou int pyglet)
        italic(bool, optional): italique
        underline(Color, optional): couleur du soulignement
        color(Color, optional): couleur du texte (Color)
        opacity(Real, optional): opacité globale [0.0 ; 1.0]
        width(int, optional): largeur de la boîte en pixels (None = pas de boîte)
        height(int, optional): hauteur de la boîte en pixels (None = pas de boîte)
        multiline(bool, optional): autorise les \\n explicites
        line_spacing(int, optional): espacement entre les lignes en pixels (None = défaut)
        wrap_lines(bool, optional): word-wrap automatique (nécessite width)
        align(HorizontalAlign, optional): alignement horizontal
        margin(int, optional): marge intérieure uniforme en pixels
    """
    __slots__ = (
        "_text",
        "_position", "_anchor", "_rotation",
        "_weight", "_italic", "_underline",
        "_color", "_opacity",
        "_width", "_height",
        "_multiline", "_line_spacing", "_wrap_lines",
        "_align", "_margin",
    )
    
    def __init__(
            self,
            text: Text,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            rotation: Real = 0.0,
            weight: str = "normal",
            italic: bool = False,
            underline: Color = None,
            color: Color = (255, 255, 255),
            opacity: Real = 1.0,
            width: int = None,
            height: int = None,
            multiline: bool = False,
            line_spacing: int = None,
            wrap_lines: bool = False,
            align: HorizontalAlign = "left",
            margin: int = 0,
        ):
        super().__init__(position, anchor, opacity)

        # Texte
        self._text: Text = expect(text, Text)
        self._text_renderer: PygletLabelRenderer = None

        # Transform
        self._rotation: float = float(expect(rotation, Real))

        # Style
        self._weight: str = expect(weight, str)
        self._italic: bool = expect(italic, bool)
        self._underline: Color = Color(underline) if underline is not None else None

        # Affichage
        self._color: Color = Color(color)

        # Mise en page
        self._width: int = expect(width, int)
        self._height: int = expect(height, int)
        self._multiline: bool = expect(multiline, bool)
        self._line_spacing: int = expect(line_spacing, (int, None))
        self._wrap_lines: bool = expect(wrap_lines, bool)
        self._align: HorizontalAlign = expect(align, HorizontalAlign)
        self._margin: int = expect(margin, int)
    
    # ======================================== PROPERTIES ========================================
    @property
    def text(self) -> Text:
        """Texte interne à rendre

        Le texte doit être un Asset Texte
        """
        return self._text
    
    @text.setter
    def text(self, value: Text) -> None:
        self._text = expect(value, Text)

    @property
    def rotation(self) -> float:
        """Rotation en degrés

        La rotation doit être un Réel
        """
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(expect(value, Real))

    @property
    def weight(self) -> str:
        """Graisse de la police

        La graisse doit être un string conforme à la norme CSS
        """
        return self._weight
    
    @weight.setter
    def weight(self, value: str) -> None:
        self._weight = expect(value, str)

    @property
    def italic(self) -> bool:
        """Mise en italique de la police

        Cette propriété fixe l'utilisation ou non de l'italique
        """
        return self._italic
    
    @italic.setter
    def italic(self, value: bool) -> None:
        self._italic = expect(value, bool)

    @property
    def underline(self) -> Color:
        """Couleur de soulignage du texte

        La couleur de soulignage doit être un Asset Color ou un tuple rgb/rgba
        Mettre à None pour ne pas souligner le texte
        """
        return self._underline
    
    @underline.setter
    def underline(self, value: Color) -> None:
        self._underline = Color(value) if value is not None else None