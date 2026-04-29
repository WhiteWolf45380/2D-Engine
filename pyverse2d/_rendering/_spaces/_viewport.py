# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, positive
from ...abc import Space
from ...math import Point, Vector

from pyglet.math import Mat4

from numbers import Real

# ======================================== VIEWPORT ========================================
class Viewport(Space):
    """Zone de l'espace logique

    Args:
        position: position du coin bas gauche du viewport
        width: largeur en pixels logiques (None = tout)
        height: hauteur en pixels logiques (None = tout)
        origin: origine locale relative du viewport *((0.5, 0.5) = centre)*
        direction: direction locale des coordonnées
    """
    __slots__ = (
        "_position",
        "_width", "_height",
        "_origin", "_direction",
    )

    _VIEWPORT_CACHE: dict[tuple, Mat4] = {}

    def __init__(
        self,
        position: Point = (0.0, 0.0),
        width: Real = 0.0,
        height: Real = 0.0,
        origin: Point = (0.0, 0.0),
        direction: Vector = (1.0, 1.0),
    ):
        # Transtypage
        position = Point(position)
        width = float(width)
        height = float(height)
        origin = Point(origin)
        direction = Vector(direction)

        # Debugging
        if __debug__:
            positive(width, arg="width")
            positive(height, arg="height")

        # Attributs publiques
        self._position: Point = position
        self._width: float = width
        self._height: float = height
        self._origin: Point = origin
        self._direction: Vector = direction

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position du coin bas gauche

        La position peut-être un objet mathématique ``Point`` ou un tuple ``(x, y)``
        """
        return self._position
    
    @position.setter
    def position(self, value: Point):
        self._position.x, self._position.y = value

    @property
    def x(self) -> float:
        """Cordonnée horizontale du coin bas gauche
        
        La valeur doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real):
        self._position.x = value

    @property
    def y(self) -> float:
        """Coordonnée verticale du coin bas gauche

        La valeur doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real):
        self._position.y = value

    @property
    def width(self) -> float:
        """Largeur du viewport
        
        La largeur doit être un ``Réel`` positif non nul.
        """
        return self._width
    
    @width.setter
    def width(self, value: Real):
        value = float(value)
        assert value >= 0.0, f"width ({value}) must be positive"
        self._width = value

    @property
    def height(self) -> float:
        """Hauteur du viewport
        
        La hauteur doit être un ``Réel`` positif non nul.
        """
        return self._height
    
    @height.setter
    def height(self, value: Real):
        value = float(value)
        assert value >= 0.0, f"heighr ({value}) must be positive"
        self._height = value

    @property
    def origin(self) -> Point:
        """Origine relative du viewport

        L'origine peut être un objet ``Point`` ou un tuple ``(ox, oy)``.
        Les coordonnées de l'origine doivent être dans l'intervalle [0, 1].
        """
        return self._origin
    
    @origin.setter
    def origin(self, value: Point) -> None:
        self._origin.x, self._origin.y = value

    @property
    def direction(self) -> Vector:
        """Vecteur directionnel des coordonnées

        Le vecteur peut être un objet ``Vector`` ou un tuple ``(dx, dy)``
        """
        return self._direction

    @direction.setter
    def direction(self, value: Vector) -> None:
        self._direction.x, self._direction.y = value

    # ======================================== COLLECTIONS ========================================
    def copy(self) -> Viewport:
        """Crée une copie du viewport"""
        return Viewport(
            position = self._position,
            width = self._width,
            height = self._height,
            origin = self._origin,
            direction = self._direction,
        )
    
    # ======================================== RESOLVE ========================================
    def resolve(self, fb_width: int, fb_height: int) -> tuple[int, int, int, int]:
        """Renvoie le viewport résolu dans le Framebuffer
        
        Args:
            fb_width: largeur du framebuffer
            fb_height: hauteur du framebuffer
        """
        x = int(self._position.x)
        y  = int(self._position.y)
        width = int(self._width) if self._width != 0.0 else fb_width
        height = int(self._height) if self._height != 0.0 else fb_height
        return x, y, width, height

    # ======================================== COMPUTE ========================================
    def viewport_matrix(self) -> Mat4:
        """Renvoie la matrice du viewport"""
        # Renommage
        ox, oy = self._origin
        dx, dy = self._direction

        # Cache
        viewport_key: tuple = (ox, oy, dx, dy)
        if viewport_key in self._VIEWPORT_CACHE:
            return self._VIEWPORT_CACHE[viewport_key]
        
        # Construction
        matrix = self._compute_viewport(ox, oy, dx, dy)
        self._VIEWPORT_CACHE = matrix
        return matrix
    
    # ======================================== INTERNALS ========================================
    def _compute_viewport(self, ox: float, oy: float, dx: float, dy: float) -> Mat4:
        """Compute la matrice du viewport *(TS)^(-1)*

        Espace: *NDC* to *NDC*

        Args:
            ox: origine horizontale relative locale du viewport
            oy: origine verticale relative locale du viewport
            dx: composante x du vecteur directionnel
            dy: composante y du vecteur directionnel
        """
        # Calcul des paramètres
        tx = ox
        ty = oy
        sx = dx
        sy = dx

        # Construction de la matrice
        return Mat4(
            1/sx, 0,  0, -tx,
            0,  1/sy, 0, -ty,
            0,  0,  1, 0,
            0,  0,  0, 1,
        )