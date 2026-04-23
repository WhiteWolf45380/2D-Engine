# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import positive
from ..abc import Asset

from pyglet import media as _media

from typing import TYPE_CHECKING
from numbers import Real

if TYPE_CHECKING:
    from .._managers._audio import AudioManager

# ======================================== ASSET ========================================
class Music(Asset):
    """Musique streamée depuis le disque.

    Args:
        path:   chemin vers le fichier audio
        volume: volume propre [0, 1]
    """
    __slots__ = (
        "_path", "_volume",
        "_player", "_playing", "_loop",
    )

    _AUDIO_MANAGER: AudioManager = None

    @classmethod
    def _get_audio_manager(cls) -> AudioManager:
        """Renvoie le gestionnaire audio"""
        if cls._AUDIO_MANAGER is None:
            from .._managers._audio import AudioManager
            cls._AUDIO_MANAGER = AudioManager
        return cls._AUDIO_MANAGER

    def __init__(self, path: str, volume: Real = 1.0):
        # Attributs publiques
        self._path: str = path
        self._volume: float = float(volume)

        if __debug__:
            positive(self._volume)

        # Attributs internes
        self._player: _media.Player | None = None
        self._playing: bool = False
        self._loop: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def path(self) -> str:
        """Chemin du fichier audio"""
        return self._path
    
    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def volume(self) -> float:
        """Volume propre
        
        Le volume doit être un ``Réel``positif.
        """
        return self._volume

    @volume.setter
    def volume(self, value: Real) -> None:
        value = float(value)
        assert value >= 0.0, f"volume ({value}) must be positive"
        self._volume = value
        if self._player:
            self._player.volume = self._volume

    # ======================================== PREDICATES ========================================
    def is_playing(self) -> bool:
        """Vérifie que la musique soit en cours de lecture"""
        return self._playing

    # ======================================== INTERFACE ========================================
    def play(self, loop: bool = True, fade_s: Real = 0.0) -> None:
        """Joue la musique

        Args:
            loop: boucle infinie si True
            fade_s: durée du fade-in en secondes
        """
        self._get_audio_manager().play_music(self, loop=loop, fade_s=fade_s)

    def stop(self, fade_s: Real = 0.0) -> None:
        """Arrête la musique.

        Args:
            fade_s: durée du fade-out (géré par le manager)
        """
        self._get_audio_manager().stop_music(self, fade_s=fade_s)

    def _set_volume(self, value: float) -> None:
        """Volume brut sur le player"""
        if self._player:
            self._player.volume = value