# ======================================== IMPORTS ========================================
from __future__ import annotations

from pyglet import media as _media

from typing import Callable, Any
from abc import ABC, abstractmethod

# ======================================== ABSTRACT CLASS ========================================
class AudioHandle(ABC):
    """Classe abstraite des tokens audio"""
    __slots__ = (
        "source", "player", "on_stop",
        "base_volume",
        "_active",
        "__weakref__",
    )

    def __init__(self, source: _media.StaticSource, player: _media.Player, on_stop: Callable[[AudioHandle], Any] = None):
        # Attributs publiques
        self.source: _media.StreamingSource = source
        self.player: _media.Player = player
        self.on_stop: Callable[[AudioHandle], Any] = on_stop
        
        self.base_volume: float = 1.0

        # Attributs internes
        self._active: bool = True

        # Configuration du player
        self.player.push_handlers(on_player_eos=self.on_eos)

    # ======================================== GETTERS ========================================
    def get_play_volume(self) -> float:
        """Renvoie le volume ponctuel"""
        return (self.player.volume / self.base_volume) if self.base_volume > 0.0 else 0.0

    # ======================================== SETTERS ========================================
    def set_play_volume(self, value: float) -> None:
        """Fixe le volume ponctuel"""
        if self._active:
            new_volume = self.base_volume * value
            if new_volume == self.player.volume:
                return
            self.player.volume = new_volume
    
    # ======================================== PREDICATES ========================================
    def is_active(self) -> bool:
        """Vérifie que le handle soit actif"""
        return self._active

    def is_playing(self) -> bool:
        """Vérifie que le handle soit en cours de lecture"""
        return self._active and self.player.playing
    
    # ======================================== HOOKS ========================================
    @abstractmethod
    def on_eos(self) -> None: ...

    # ======================================== INTERFACE ========================================
    @abstractmethod
    def resume(self) -> None: ...

    @abstractmethod
    def pause(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    def delete(self) -> None:
        """Supprime le player sans déclencher les événements d'arrêt"""
        if self._active:
            self.player.pause()
            self.player.delete()
            self._active = False
    
    # ======================================== INTERNALS ========================================
    def _set_volume(self, value: float) -> None:
        """Fixe le volum brute"""
        if self._active:
            self.player.volume = value