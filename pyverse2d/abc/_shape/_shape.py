# ======================================== IMPORTS ========================================
from ...math import Point

from abc import ABC, abstractmethod
from typing import Iterator, Self, Any
import math

# ======================================== CLASSE ABSTRAITE ========================================
class Shape(ABC):
    """Classe abstraite des formes"""
    def __init__(self):
        ...
    
    # ======================================== CONVERSIONS ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __iter__(self) -> Iterator: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    # ======================================== GETTERS ========================================
    @property
    @abstractmethod
    def perimeter(self) -> float: ...

    @property
    @abstractmethod
    def area(self) -> float: ...

    @property
    @abstractmethod
    def bounding_box(self) -> tuple[float, float, float, float]: ...

    # ======================================== COMPARATORS ========================================
    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...

    # ======================================== PREDICATES ========================================
    @abstractmethod
    def contains(self, point: Point) -> bool: ...

    def world_contains(self, point, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0, anchor_x: float = 0.5, anchor_y: float = 0.5) -> bool:
        """Teste si un point monde est dans la shape"""
        xmin, ymin, xmax, ymax = self.bounding_box
        ox = xmin + anchor_x * (xmax - xmin)
        oy = ymin + anchor_y * (ymax - ymin)

        px, py = float(point[0]) - x + ox, float(point[1]) - y + oy
        if rotation:
            rad = math.radians(rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            px, py = px * cos_r + py * sin_r, -px * sin_r + py * cos_r
        if scale != 1.0:
            px /= scale
            py /= scale
        return self.contains((px, py))

    # ======================================== PUBLIC METHODS ========================================
    @abstractmethod
    def copy(self) -> Self: ...

    @abstractmethod
    def scale(self, factor: float): ...

    @abstractmethod
    def world_bounding_box(self, x: float, y: float, scale: float, rotation: float) -> tuple[float, float, float, float]: ...