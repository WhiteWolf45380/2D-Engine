# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, HasPosition
from ...abc import System

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