# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod

# ======================================== OBJET ========================================
class Request(ABC):
    """Requête contenant un jeu d'informations"""
    @abstractmethod
    def __init__(self):
        ...