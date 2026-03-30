# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..math import Point, Vector
from ..world import Entity, Transform

from pyglet.math import Mat4, Vec3
from numbers import Real

# ======================================== CAMERA ========================================
class Camera:
    """
    Définit le point de vue dans le monde

    Args:
        position(Point): position de la caméra
        zoom (Real): facteur de zoom
    """
    __slots__ = ("_position", "_following", "_offset", "_zoom")

    def __init__(self, position: Point = (0.0, 0.0), zoom: Real = 1.0):
        self._position: Point = Point(position)
        self._following: Entity | None = None
        self._offset: Vector = Vector(0.0, 0.0)
        self._zoom: float = float(positive(not_null(expect(zoom, Real))))

    # ======================================== GETTERS ========================================
    @property
    def position(self) -> Point:
        """Renvoie la position"""
        return self._position

    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._position.x

    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._position.y

    @property
    def offset(self) -> Vector:
        """Renvoie le vecteur de décalage à la position"""
        return self._offset
    
    @property
    def offset_x(self) -> float:
        """Renvoie le décalage horizontal"""
        return self._offset.x
    
    @property
    def offset_y(self) -> float:
        """Renvoie le décalage vertical"""
        return self._offset.y
    
    @property
    def final_x(self) -> float:
        """position horizontale finale"""
        self._check_follow()
        base = self._following.get(Transform).x if self._following else self._position.x
        return base + self._offset.x
    
    @property
    def final_y(self) -> float:
        """position verticale finale"""
        self._check_follow()
        base = self._following.get(Transform).y if self._following else self._position.y
        return base + self._offset.y

    @property
    def final_position(self) -> Point:
        """Renvoie la position finale"""
        self._check_follow()
        base = self._following.get(Transform).position if self._following else self._position
        return base + self._offset

    @property
    def zoom(self) -> float:
        return self._zoom

    # ======================================== SETTERS ========================================
    @position.setter
    def position(self, value: Point):
        """Fixe la position"""
        self._position = Point(value)

    @x.setter
    def x(self, value: Real):
        """Fixe la position horizontale"""
        self._position._x = float(expect(value, Real))

    @y.setter
    def y(self, value: Real):
        """Fixe la position verticale"""
        self._position._y = float(expect(value, Real))
    
    @offset.setter
    def offset(self, value: Vector) -> None:
        """Fixe le décalage"""
        self._offset = Vector(value)
    
    @offset_x.setter
    def offset_x(self, value: Real) -> None:
        """Fixe le décalage horizontal"""
        self._offset._x = float(expect(value, Real))
    
    @offset_y.setter
    def offset_y(self, value: Real) -> None:
        """Fixe le décalage vertical"""
        self._offset_y = float(expect(value, Real))

    @zoom.setter
    def zoom(self, value: Real):
        """Fixe le facteur de zoom"""
        self._zoom = positive(not_null(float(expect(value, Real))))
    
    # ======================================== DÉPLACEMENT ========================================
    def move(self, vector: Vector):
        """
        Déplace la position manuelle de la camera

        Args:
            vector(Vector): vecteur de translation
        """
        self._position += Vector(vector)

    # ======================================== FOLLOW ========================================
    def follow(self, entity: Entity):
        """
        Suit le Transform d'une entité

        Args:
            entity (Entity): entité à suivre
        """
        if not entity.has(Transform):
            raise ValueError(f"Entity {entity.id[:8]}... has no Transform component")
        self._following = entity

    def unfollow(self):
        """Détache la camera de l'entité suivie"""
        self._position = self._following.get(Transform).position.copy()
        self._following = None

    def _check_follow(self):
        """Unfollow automatique si l'entité est inactive"""
        if self._following is not None and not self._following.is_active():
            self._following = None

    # ======================================== RENDU ========================================
    def view_matrix(self) -> Mat4:
        """Produit la matrice de vue à appliquer à l'écran"""
        fx, fy = self.final_position
        translate = Mat4.from_translation(Vec3(-fx, -fy, 0))
        scale = Mat4.from_scale(Vec3(self._zoom, self._zoom, 1))
        return translate @ scale
    
    def zoom_matrix(self) -> Mat4:
        """Produit uniquement la matrice de zoom à appliquer à l'écran"""
        return Mat4.from_scale(Vec3(self._zoom, self._zoom, 1))