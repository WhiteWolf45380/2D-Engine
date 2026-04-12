# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped, over
from ...abc import Component
from ...math import Vector

from typing import TYPE_CHECKING, Iterator
from numbers import Real

if TYPE_CHECKING:
    from .._entity import Entity

# ======================================== COMPONENT ========================================
class Follow(Component):
    """``Component`` gérant le suivi

    Ce composant est manipulé par ``SteeringSystem``.

    Args:
        entity: ``Entité`` à suivre
        offset: ``Vecteur`` de décalage par rapport à la cible
        smoothing: facteur de retard relatif [0, 1[ — uniquement cas cinématique
        force: force d'attraction en Newtons — uniquement cas dynamique
        damping: coefficient d'amortissement de la vélocité — uniquement cas dynamique.
                 Applique une force opposée à la vélocité, permettant une décélération
                 progressive sans arrêt brutal. Plus la valeur est élevée, plus le
                 ralentissement est fort.
        radius_min: borne intérieure de la zone de tolérance.
                    En dessous, force répulsive. Doit être <= radius_max.
        radius_max: borne extérieure de la zone de tolérance.
                    Au delà, force attractive. 0 = pile sur la cible.
        dot_min: composante alignée minimale acceptable par rapport à l'offset [-1, 1].
        cross_min: composante latérale minimale acceptable [-1, 1].
        cross_max: composante latérale maximale acceptable [-1, 1].
        axis_x: activer le suivi horizontal
        axis_y: activer le suivi vertical
    """
    __slots__ = (
        "_entity", "_offset",
        "_smoothing", "_force", "_damping",
        "_radius_min", "_radius_max",
        "_dot_min", "_cross_min", "_cross_max",
        "_axis_x", "_axis_y",
    )
    requires = ("Transform",)

    def __init__(
            self,
            entity: Entity,
            offset: Vector = (0.0, 0.0),
            smoothing: Real = 0.0,
            force: Real = 5000.0,
            damping: Real = 0.0,
            radius_min: Real = 0.0,
            radius_max: Real = 0.0,
            dot_min: Real = -1.0,
            cross_min: Real = -1.0,
            cross_max: Real = 1.0,
            axis_x: bool = True,
            axis_y: bool = True,
        ):
        from .._entity import Entity
        self._entity: Entity = expect(entity, Entity)
        self._offset: Vector = Vector(offset)
        self._smoothing: float = clamped(float(expect(smoothing, Real)), include_max=False)
        self._force: float = over(float(expect(force, Real)), 0.0, include=False)
        self._damping: float = abs(float(expect(damping, Real)))
        r_min = abs(float(expect(radius_min, Real)))
        r_max = abs(float(expect(radius_max, Real)))
        assert r_min <= r_max, ValueError(f"radius_min ({r_min}) doit être inférieur ou égal à radius_max ({r_max})")
        self._radius_min: float = r_min
        self._radius_max: float = r_max
        self._dot_min: float = float(clamped(expect(dot_min, Real), min=-1))
        self._cross_min: float = float(clamped(expect(cross_min, Real), min=-1))
        self._cross_max: float = float(clamped(expect(cross_max, Real), min=-1))
        self._axis_x: bool = expect(axis_x, bool)
        self._axis_y: bool = expect(axis_y, bool)

        assert self._entity.has("Transform"), ValueError(f"Entity {self._entity.id}... has no Transform component")

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"Follow(entity={self._entity.id[:8]}..., offset={self._offset}, force={self._force})"

    def __iter__(self) -> Iterator:
        return iter(self.get_attributes())

    def __hash__(self) -> int:
        return hash(self.get_attributes())

    def get_attributes(self) -> tuple:
        return (
            self._entity, self._offset,
            self._smoothing, self._force, self._damping,
            self._radius_min, self._radius_max,
            self._dot_min, self._cross_min, self._cross_max,
            self._axis_x, self._axis_y,
        )

    # ======================================== PROPERTIES ========================================
    @property
    def entity(self) -> Entity:
        """Entité à suivre

        L'entité doit être un objet ``Entity`` avec un composant ``Transform``.
        """
        return self._entity

    @entity.setter
    def entity(self, value: Entity) -> None:
        from .._entity import Entity
        self._entity = expect(value, Entity)
        if not self._entity.has("Transform"):
            raise ValueError(f"Entity {self._entity.id}... has no Transform component")

    @property
    def offset(self) -> Vector:
        """Décalage par rapport à la cible

        Le décalage peut être un objet ``Vector`` ou un tuple ``(vx, vy)``.
        """
        return self._offset

    @offset.setter
    def offset(self, value: Vector) -> None:
        self._offset = Vector(value)

    @property
    def smoothing(self) -> float:
        """Facteur de retard pour le cas cinématique

        Le facteur doit être un ``Réel`` compris dans l'intervalle [0, 1[.
        Plus la valeur est élevée, plus le suivi est progressif.
        Ignoré dans le cas dynamique (rigidbody).
        """
        return self._smoothing

    @smoothing.setter
    def smoothing(self, value: Real) -> None:
        self._smoothing = clamped(float(expect(value, Real)), include_max=False)

    @property
    def force(self) -> float:
        """Force d'attraction en Newtons — cas dynamique uniquement

        La force doit être un ``Réel`` positif non nul.
        """
        return self._force

    @force.setter
    def force(self, value: Real) -> None:
        self._force = over(float(expect(value, Real)), 0.0, include=False)

    @property
    def damping(self) -> float:
        """Coefficient d'amortissement de la vélocité — cas dynamique uniquement

        Applique une force opposée à la vélocité à chaque frame, provoquant
        une décélération progressive. Plus la valeur est élevée, plus le
        ralentissement est fort. 0 = pas d'amortissement.
        """
        return self._damping

    @damping.setter
    def damping(self, value: Real) -> None:
        self._damping = abs(float(expect(value, Real)))

    @property
    def radius_min(self) -> float:
        """Borne intérieure de la zone de tolérance

        En dessous de cette distance, une force répulsive est appliquée.
        Doit être inférieur ou égal à radius_max.
        """
        return self._radius_min

    @radius_min.setter
    def radius_min(self, value: Real) -> None:
        r = abs(float(expect(value, Real)))
        if r > self._radius_max:
            raise ValueError(f"radius_min ({r}) doit être inférieur ou égal à radius_max ({self._radius_max})")
        self._radius_min = r

    @property
    def radius_max(self) -> float:
        """Borne extérieure de la zone de tolérance

        Au delà de cette distance, une force attractive est appliquée.
        0 = pile sur la cible. Doit être supérieur ou égal à radius_min.
        """
        return self._radius_max

    @radius_max.setter
    def radius_max(self, value: Real) -> None:
        r = abs(float(expect(value, Real)))
        if r < self._radius_min:
            raise ValueError(f"radius_max ({r}) doit être supérieur ou égal à radius_min ({self._radius_min})")
        self._radius_max = r

    @property
    def dot_min(self) -> float:
        """Composante alignée minimale acceptable [-1, 1]

        1 = exactement dans la direction de l'offset, -1 = direction opposée.
        """
        return self._dot_min

    @dot_min.setter
    def dot_min(self, value: Real) -> None:
        self._dot_min = float(clamped(expect(value, Real)))

    @property
    def cross_min(self) -> float:
        """Composante latérale minimale acceptable [-1, 1]

        0 = aligné, -1 = 90° à droite.
        """
        return self._cross_min

    @cross_min.setter
    def cross_min(self, value: Real) -> None:
        self._cross_min = float(clamped(expect(value, Real)))

    @property
    def cross_max(self) -> float:
        """Composante latérale maximale acceptable [-1, 1]

        0 = aligné, 1 = 90° à gauche.
        """
        return self._cross_max

    @cross_max.setter
    def cross_max(self, value: Real) -> None:
        self._cross_max = float(clamped(expect(value, Real)))

    @property
    def axis_x(self) -> bool:
        """Suivi horizontal actif"""
        return self._axis_x

    @axis_x.setter
    def axis_x(self, value: bool) -> None:
        self._axis_x = expect(value, bool)

    @property
    def axis_y(self) -> bool:
        """Suivi vertical actif"""
        return self._axis_y

    @axis_y.setter
    def axis_y(self, value: bool) -> None:
        self._axis_y = expect(value, bool)