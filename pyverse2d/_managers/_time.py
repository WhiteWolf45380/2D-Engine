# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Manager

from ._context import ContextManager

# ======================================== GESTIONNAIRE ========================================
class TimeManager(Manager):
    """Gestionnaire du temps"""
    __slots__ = ()

    def __init__(self, context_manager: ContextManager):
        # Initialisation du gestionnaire
        super().__init__(context_manager)

    def _compute_dt(self, raw_dt: float) -> float:
        """Calcul le delta-time affiné"""
        return raw_dt
    
# ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        ...

    def flush(self) -> None:
        """Nettoyage"""
        ...