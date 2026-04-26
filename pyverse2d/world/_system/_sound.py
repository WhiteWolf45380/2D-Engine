# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, HasPosition
from ...abc import System

from .._world import World
from .._component import SoundEmitter, Transform

# ======================================== SYSTEM ========================================
class SoundSystem(System):
    """Système gérant les composants ``SoundEmitter``

    Ce système est automatiquement ajouté à la scène.

    Args:
        origin: référentiel de position pour les sons (généralement la caméra)
    """
    __slots__ = ()

    order = 110
    exclusive = False

    def __init__(self, origin: HasPosition):
        self._origin: HasPosition = origin

        if __debug__:
            expect(origin, HasPosition)

    # ======================================== CONTRACT ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du système"""
        return f"SoundSystem(origin={(self._origin.x, self._origin.y)})"
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, world: World,dt: float) -> None:
        """Met à jour les sons émis"""
        for entity in world.query(SoundEmitter):
            se = entity.sound_emitter