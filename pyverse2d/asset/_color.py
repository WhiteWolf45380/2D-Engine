# ======================================== IMPORTS ========================================
from __future__ import annotations
from ..abc import Asset
from typing import Union, Tuple

class Color(tuple, Asset):
    """
    Descripteur de couleur
    Accepte les composantes soit en float [0.0; 1.0], soit en int [0; 255]

    Supports:
        Color(Color)
        Color(r, g, b, a)
        Color(r, g, b)
        Color((r, g, b, a))
        Color((r, g, b))
    """
    __slots__ = ("_r", "_g", "_b", "_a")

    def __new__(cls, *args, argument: str = "Argument"):
        # Color(Color)
        if len(args) == 1 and isinstance(args[0], cls):
            return args[0]

        # Tuple ou séquence
        if len(args) == 1 and isinstance(args[0], tuple):
            value = args[0]
            n = len(value)
            if n < 3:
                raise ValueError(f"{argument} must have at least 3 elements")
            r, g, b = value[:3]
            a = value[3] if n >= 4 else 1.0

        # Color(r, g, b) ou Color(r, g, b, a)
        elif 3 <= len(args) <= 4:
            r, g, b = args[:3]
            a = args[3] if len(args) == 4 else 1.0
        else:
            raise TypeError(f"{argument}: invalid arguments {args}")

        # Conversion en float
        r = cls._to_float(r, "red", argument)
        g = cls._to_float(g, "green", argument)
        b = cls._to_float(b, "blue", argument)
        a = cls._to_float(a, "alpha", argument)

        self = tuple.__new__(cls, (r, g, b, a))
        self._r, self._g, self._b, self._a = r, g, b, a
        return self
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de la couleur"""
        return f"Color(r={self._r:.3f}, g={self._g:.3f}, b={self._b:.3f}, a={self._a:.3f})"

    # ======================================== GETTERS ========================================
    @property
    def r(self) -> float:
        """Renvoie la composante rouge"""
        return self._r

    @property
    def g(self) -> float:
        """Renvoie la composante verte"""
        return self._g

    @property
    def b(self) -> float:
        """Renvoie la composante bleu"""
        return self._b

    @property
    def a(self) -> float:
        """Renvoie la composante alpha"""
        return self._a

    @property
    def rgb(self) -> Tuple[float, float, float]:
        """Renvoie les composantes RGB avec composantes float[0.0; 1.0]"""
        return self._r, self._g, self._b

    @property
    def rgba(self) -> Tuple[float, float, float, float]:
        """Renvoie les composantes RGBA avec composantes float[0.0; 1.0]"""
        return self._r, self._g, self._b, self._a

    @property
    def rgb8(self) -> Tuple[int, int, int]:
        """Renvoie la couleur RGB avec composantes int[0; 255]"""
        return int(round(self._r * 255)), int(round(self._g * 255)), int(round(self._b * 255))

    @property
    def rgba8(self) -> Tuple[int, int, int, int]:
        """Renvoie la couleur RGBA avec composantes int[0; 255]"""
        return int(round(self._r * 255)), int(round(self._g * 255)), int(round(self._b * 255)), int(round(self._a * 255))

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Color:
        """Renvoie une copie de la couleur"""
        return Color(self._r, self._g, self._b, self._a)

    def copy(self) -> Color:
        """Renvoie une copie de la couleur"""
        return self.__copy__()

    # ======================================== INTERNALS ========================================
    @staticmethod
    def _to_float(v: Union[int, float], name: str, argument: str) -> float:
        if isinstance(v, int):
            if not (0 <= v <= 255):
                raise ValueError(f"{argument}: {name} out of range ({v})")
            return v / 255.0
        elif isinstance(v, float):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{argument}: {name} out of range ({v})")
            return v
        else:
            raise TypeError(f"{argument}: invalid {name} type {type(v).__name__}")