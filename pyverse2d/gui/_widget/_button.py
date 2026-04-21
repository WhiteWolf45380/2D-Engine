# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, positive
from ..._rendering import PygletShapeRenderer, PygletSpriteRenderer, PygletLabelRenderer
from ...abc import Widget, Shape
from ...math import Point, Vector
from ...typing import BorderAlign
from ...asset import Image, Text, Color
from ...shape import Rect

from numbers import Real

# ======================================== WIDGET ========================================
class Button(Widget):
    """Composant GUI composé: Bouton
    
    Args:
        position: positionnement
        anchor: ancre relative locale
        scale: facteur de redimensionnement
        rotation: angle de rotation
        background: forme ou image du fond
        background_color: couleur de fond
        text: texte du bouton
        text_offset: décalage du texte par rapport au centre
        text_color: couleur du texte
        text_weight: graisse ('bold', 'thin', '100'…'900', ou int pyglet)
        text_italic: italique
        text_underline: couleur de soulignement
        border_width: épaisseur de la bordure
        border_align: alignement de la bordure
        border_color: couleur de la bordure
        opacity: opacité [0, 1]
        clipping: rendu des widgets enfants strictement dans le AABB de la hitbox
    """
    __slots__ = (
        "_background", "_background_color",
        "_text", "_text_color", "_text_weight", "_text_italic", "_text_underline",
        "_border_width", "_border_align", "_border_color",
        "_opacity", "_clipping",
    )

    def __init__(
            self,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            scale: Real = 1.0,
            rotation: Real = 0.0,
            background: Shape | Image = None,
            background_color: Color = (255, 255, 255),
            text: Text = None,
            text_offset: Vector = (0.0, 0.0),
            text_color: Color = (0, 0, 0),
            text_weight: str = "normal",
            text_italic: bool = False,
            text_underline: Color = None,
            border_width: int = 0,
            border_align: BorderAlign = "center",
            border_color: Color = (0, 0, 0),
            opacity: Real = 1.0,
            clipping: bool = False,
        ):
        # Initialisation du widget
        super().__init__(position, anchor, scale, rotation, opacity, clipping=clipping)

        # Attributs publiques
        self._background: Shape | Image | None = background
        self._background_color: Color = Color(background_color)
        self._text: Text = text
        self._text_offset: Vector = Vector(text_offset)
        self._text_color: Color = Color(text_color)
        self._text_weight: str = text_weight
        self._text_italic: bool = text_italic
        self._text_underline: Color = Color(text_underline) if text_underline is not None else None
        self._border_width: int = border_width
        self._border_align: BorderAlign = border_align

        if __debug__:
            expect(self._background, (Shape, Image, None))
            expect(self._text, Text)
            expect(self._text_weight, str)
            expect(self._text_italic, bool)
            positive(expect(self._border_width, int))
            expect(self._border_align, str)

        # Attributs internes
        self._has_background: bool = False
        self._background_is_shape: bool = False
        self._has_text: bool = False
        self._hitbox: Shape = None
        self._resolved: bool = False
    
        self._shape_renderer: PygletShapeRenderer | None = None
        self._sprite_renderer: PygletSpriteRenderer | None = None
        self._text_renderer: PygletLabelRenderer | None = None
    
    # ======================================== PROPERTIES ========================================
    @property
    def background(self) -> Shape | Image | None:
        """Fond

        Le fond peut être un objet ``Shape``, ``Image`` ou ``None``.
        """
        return self._background
    
    @background.setter
    def background(self, value: Shape | Image | None) -> None:
        assert value is None or isinstance(value, (Shape, Image)), f"background ({value}) must be a Shape, an Image, or None"
        self._background = value
        self._background_is_shape: bool = isinstance(self._background, Shape)
        self._invalidate_scissor()

    @property
    def background_color(self) -> Color:
        """Couleur du fond

        La couleur peut être un objet ``Color`` ou n'importe quel tuple ``(r, g, b, a)``.
        """
        return self._background_color
    
    @background_color.setter
    def background_color(self, value: Color) -> None:
        self._background_color = Color(value)

    @property
    def text(self) -> Text:
        """Texte

        Le texte doit être un objet ``Texte``.
        """
        return self._text
    
    @text.setter
    def text(self, value: Text) -> None:
        assert isinstance(value, Text), f"text ({value}) must be a Text object"
        self._text = value
        self._invalidate_scissor()

    @property
    def text_offset(self) -> Vector:
        """Décalage du texte

        Le décalage peut être un objet ``Vector`` ou n'importe quel tuple ``(dx, dy)``.
        Les composantes sont en coordonnée monde.
        """
        return self._text_offset
    
    @text_offset.setter
    def text_offset(self, value: Vector) -> None:
        self._text_offset.x, self._text_offset.y = value
    
    @property
    def text_color(self) -> Color:
        """Couleur du texte

        La couleur peut être un objet ``Color`` ou n'importque quel tuple ``(r, g, b, a)``.
        """
        return self._text_color
    
    @text_color.setter
    def text_color(self, value: Color) -> None:
        self._text_color = Color(value)

    @property
    def text_weight(self) -> str:
        """Graisse de la police

        La graisse doit être un string conforme à la norme CSS.
        """
        return self._text_weight
    
    @text_weight.setter
    def text_weight(self, value: str) -> None:
        assert isinstance(value, str), f"text_weight ({value}) must be a string"
        self._text_weight = value

    @property
    def text_italic(self) -> bool:
        """Mise en italique de la police

        Cette propriété fixe l'utilisation ou non de l'italique.
        """
        return self._text_italic
    
    @text_italic.setter
    def text_italic(self, value: bool) -> None:
        assert isinstance(value, bool), f"text_italic ({value}) must be a boolean"
        self._text_italic = value

    @property
    def text_underline(self) -> Color | None:
        """Couleur de soulignage du texte

        La couleur de soulignage peut être un asset ``Color`` ou un tuple ``(r, g, b, a)``.
        Mettre à ``None`` pour ne pas souligner le texte.
        """
        return self._text_underline
    
    @text_underline.setter
    def text_underline(self, value: Color | None) -> None:
        self._text_underline = Color(value) if value is not None else None

    @property
    def border_width(self) -> int:
        """Largeur de la bordure

        La largeur doit être un ``int`` positif.
        La bordure n'est affichée que si un background est défini.
        """
        return self._border_width

    @border_width.setter
    def border_width(self, value: int) -> None:
        assert isinstance(value, int) and value >= 0.0, f"border_width ({value}) must be a positive integer"
        self._border_width = value

    @property
    def border_align(self) -> BorderAlign:
        """Alignement de la bordure

        L'alignement doit être un ``BorderAlign``.
        """
        return self._border_align
    
    @border_align.setter
    def border_align(self, value: BorderAlign) -> None:
        assert isinstance(value, str), f"border_align ({value}) must be a BorderAlign"
        self._border_align = value

    @property
    def hitbox(self) -> Shape:
        return self._hitbox
    
    # ======================================== LIFE CYCLE ========================================
    def _update(self, dt):
        """Actualisation"""
        ...
    
    def _draw(self, pipeline, context, share_scale = True, share_rotation = True):
        """Affichage"""
        ...
    
    def _destroy(self):
        """Lièbre les ressources pyglet"""
        if self._shape_renderer:
            self._shape_renderer.delete()
        if self._sprite_renderer:
            self._sprite_renderer.delete()
        if self._text_renderer:
            self._text_renderer.delete()
    
    # ======================================== INTERNALS ========================================
    def _resolve(self) -> None:
        """Résolution du bouton"""
        if self._background is not None:
            self._has_background = True
            if isinstance(self._background, Shape):
                self._background_is_shape = True
                self._hitbox = self._background
            else:
                self._background_is_shape = False
                self._hitbox = Rect(self._background.width, self._background.height)
            self._has_text = self._text is not None
        else:
            self._has_background = False
            if self._text is not None:
                self.hitbox = Rect(self._text_renderer.content_width, self._text_renderer.content_height)
            else:
                self._has_text = False