# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import CompositeShape
from .._flag import ComponentType

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class RoundedRect(CompositeShape):
    """
    Forme géométrique 2D : Rectangle à coins arrondis

    Args:
        width(Real):  largeur totale du rectangle
        height(Real): hauteur totale du rectangle
        radius(Real): rayon des coins arrondis
    """
    __slots__ = ("_width", "_height", "_radius")

    def __init__(self, width: Real, height: Real, radius: Real):
        self._width:  float = float(positive(not_null(expect(width,  Real))))
        self._height: float = float(positive(not_null(expect(height, Real))))
        max_radius = min(self._width, self._height) * 0.5
        self._radius: float = min(max_radius, float(positive(not_null(expect(radius, Real)))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"RoundedRect(width={self._width}, height={self._height}, radius={self._radius})"

    def __str__(self) -> str:
        return f"RoundedRect[{self._width}x{self._height} r={self._radius} | area={self.area:.4g}]"

    def __iter__(self) -> Iterator[float]:
        yield self._width
        yield self._height
        yield self._radius

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def to_tuple(self) -> tuple[float, float, float]:
        return (self._width, self._height, self._radius)

    def to_list(self) -> list[float]:
        return [self._width, self._height, self._radius]

    # ======================================== GETTERS ========================================
    @property
    def width(self) -> float:
        """Renvoie la largeur totale"""
        return self._width

    @property
    def height(self) -> float:
        """Renvoie la hauteur totale"""
        return self._height

    @property
    def radius(self) -> float:
        """Renvoie le rayon des coins"""
        return self._radius

    @property
    def inner_width(self) -> float:
        """Renvoie la largeur du rectangle intérieur (sans les coins)"""
        return self._width - 2 * self._radius

    @property
    def inner_height(self) -> float:
        """Renvoie la hauteur du rectangle intérieur (sans les coins)"""
        return self._height - 2 * self._radius

    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre du rectangle arrondi"""
        # 4 droites + 4 quarts de cercle == 2 demi-périmètres rectilignes + 1 cercle complet
        return 2 * (self.inner_width + self.inner_height) + 2 * math.pi * self._radius

    @property
    def area(self) -> float:
        """Renvoie l'aire du rectangle arrondi"""
        # Rectangle central + 4 bandes latérales + 4 coins (= 1 cercle complet)
        return (self.inner_width * self.inner_height
                + 2 * self._radius * self.inner_width
                + 2 * self._radius * self.inner_height
                + math.pi * self._radius ** 2)

    # ======================================== SETTERS ========================================
    @width.setter
    def width(self, value: Real):
        """
        Fixe la largeur totale

        Args:
            value(Real): nouvelle largeur
        """
        self._width  = float(positive(not_null(expect(value, Real))))
        self._radius = min(min(self._width, self._height) * 0.5, self._radius)
        self._invalidate_cache()

    @height.setter
    def height(self, value: Real):
        """
        Fixe la hauteur totale

        Args:
            value(Real): nouvelle hauteur
        """
        self._height = float(positive(not_null(expect(value, Real))))
        self._radius = min(min(self._width, self._height) * 0.5, self._radius)
        self._invalidate_cache()

    @radius.setter
    def radius(self, value: Real):
        """
        Fixe le rayon des coins

        Args:
            value(Real): nouveau rayon
        """
        max_radius = min(self._width, self._height) * 0.5
        self._radius = min(max_radius, float(positive(not_null(expect(value, Real)))))
        self._invalidate_cache()

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        if isinstance(other, RoundedRect):
            return (self._width  == other._width
                    and self._height == other._height
                    and self._radius == other._radius)
        return False

    # ======================================== PREDICATES ========================================
    def contains(self, point) -> bool:
        """
        Teste si un point est dans le rectangle arrondi

        Args:
            point: point à tester
        """
        px, py = abs(float(point[0])), abs(float(point[1]))
        hw, hh, r = self._width * 0.5, self._height * 0.5, self._radius

        # Hors AABB
        if px > hw or py > hh:
            return False

        # Dans le rectangle intérieur étendu (croix centrale)
        if px <= hw - r or py <= hh - r:
            return True

        # Dans l'un des 4 coins arrondis
        cx, cy = hw - r, hh - r
        return (px - cx) ** 2 + (py - cy) ** 2 <= r ** 2

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> RoundedRect:
        """Renvoie une copie du rectangle arrondi"""
        return RoundedRect(self._width, self._height, self._radius)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne le rectangle arrondi

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._width  *= factor
        self._height *= factor
        self._radius *= factor
        self._invalidate_cache()

    def components(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> Iterator[tuple]:
        """Renvoie les composants du rectangle arrondi en coordonnées monde"""
        _, _, _, _, r, _, corners = self._compute_world(x, y, scale, rotation)
        for cx, cy in corners:
            yield (ComponentType.CIRCLE, cx, cy, r)
        tl, tr, br, bl = corners
        yield (ComponentType.SEGMENT, tl[0], tl[1], tr[0], tr[1], r)
        yield (ComponentType.SEGMENT, bl[0], bl[1], br[0], br[1], r)
        yield (ComponentType.SEGMENT, tl[0], tl[1], bl[0], bl[1], r)
        yield (ComponentType.SEGMENT, tr[0], tr[1], br[0], br[1], r)

    def world_bounding_box(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max) en coordonnées monde"""
        _, _, _, _, r, _, corners = self._compute_world(x, y, scale, rotation)
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        return min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r

    # ======================================== INTERNALS ========================================
    def _compute_world(self, x: float, y: float, scale: float, rotation: float) -> tuple:
        """Calcule les paramètres monde du rectangle arrondi"""
        hx  = self.inner_width  * 0.5 * scale
        hy  = self.inner_height * 0.5 * scale
        r   = self._radius * scale

        rad   = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        def rotate(lx: float, ly: float) -> tuple[float, float]:
            return (x + lx * cos_r + ly * sin_r,
                    y - lx * sin_r + ly * cos_r)

        corners = [
            rotate(-hx,  hy),
            rotate( hx,  hy),
            rotate( hx, -hy),
            rotate(-hx, -hy),
        ]
        return (x, y, hx, hy, r, rotation, corners)