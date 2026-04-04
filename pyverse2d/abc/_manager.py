# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering import Window
    from .._managers import ContextManager

# ======================================== ABSTRACT CLASS ========================================
class Manager(ABC):
    """Classe abstraite des managers"""
    __slots__ = ("_ctx", "_window")

    def __init__(self, context_manager: ContextManager):
        # Manager des gestionnaires
        self._ctx: ContextManager = context_manager

        # Fenêtre
        self._window: Window = None

    # ======================================== BIND WINDOW ========================================
    def bind(self, window: Window) -> None:
        """Lie le gestionnaire à une fenêtre

        Args:
            window: fenêtre à assigner
        """
        self._window = window
        
    # ======================================== LIFE CYCLE ========================================
    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...