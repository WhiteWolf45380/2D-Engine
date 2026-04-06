# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import System

# ======================================== SYSTEM ========================================
class SteeringSystem(System):
    """Système gérant le pilotage positionnel"""
    __slots__ = ()
    order = 0
    exclusive = True