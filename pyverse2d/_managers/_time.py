# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Manager

from ._context import ContextManager

# ======================================== GESTIONNAIRE ========================================
class TimeManager(Manager):
    """Gestionnaire du temps"""
    __slots__ = (
        "_ctx",
    )

    def __init__(self, context_manager: ContextManager):
        # Contexte de managers
        self._ctx: ContextManager = context_manager

    def _compute_dt(self, raw_dt: float) -> float:
        """Calcul le delta-time affiné"""
        return raw_dt

    def update(self, dt: float) -> None:
        """Actualisation"""
        ...