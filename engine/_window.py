# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.math import Mat4
from pyglet.window import Window

from numbers import Real

# ======================================== WINDOW ========================================
class Window:
    """
    Fenêtre avec résolution virtuelle fixe

    Args:
        virtual_width (int): largeur de l'espace de travail virtuel
        virtual_height (int): hauteur de l'espace de travail virtuel
        title (str): titre de la fenêtre
        window_width (int): largeur initiale de la fenêtre réelle
        window_height (int): hauteur initiale de la fenêtre réelle
    """

    def __init__(
        self,
        virtual_width: int = 1920,
        virtual_height: int = 1080,
        title: str = "",
        window_width: int = 1280,
        window_height: int = 720,
    ):
        self._virtual_width: int = int(virtual_width)
        self._virtual_height: int = int(virtual_height)

        self._window = Window(
            width=window_width,
            height=window_height,
            caption=title,
            resizable=True,
        )

        self._viewport: tuple[int, int, int, int] = (0, 0, window_width, window_height)
        self._apply_projection(window_width, window_height)

        @self._window.event
        def on_resize(width: int, height: int):
            self._apply_projection(width, height)

    # ======================================== PROJECTION ========================================
    def _apply_projection(self, win_w: int, win_h: int):
        """Recalcule le viewport et la projection orthogonale"""
        virt_ratio = self._virtual_width / self._virtual_height
        win_ratio  = win_w / win_h

        if win_ratio > virt_ratio:
            h = win_h
            w = int(h * virt_ratio)
            x = (win_w - w) // 2
            y = 0
        else:
            w = win_w
            h = int(w / virt_ratio)
            x = 0
            y = (win_h - h) // 2

        self._viewport = (x, y, w, h)
        gl.glViewport(x, y, w, h)

        # Projection orthogonale
        self._window.projection = Mat4.orthogonal_projection(
            left=0, right=self._virtual_width,
            bottom=0, top=self._virtual_height,
            z_near=-1, z_far=1,
        )

    # ======================================== GETTERS ========================================
    @property
    def virtual_width(self) -> int:
        """Largeur de l'espace virtuel"""
        return self._virtual_width

    @property
    def virtual_height(self) -> int:
        """Hauteur de l'espace virtuel"""
        return self._virtual_height

    @property
    def width(self) -> int:
        """Largeur de la fenêtre réelle"""
        return self._window.width

    @property
    def height(self) -> int:
        """Hauteur de la fenêtre réelle"""
        return self._window.height

    @property
    def native(self) -> Window:
        """Fenêtre pyglet brute — usage interne uniquement"""
        return self._window

    # ======================================== CONVERSIONS DE COORDONNÉES ========================================
    def window_to_virtual(self, x: float, y: float) -> tuple[float, float]:
        """
        Convertit des coordonnées réelles en coordonnées virtuelles

        Args:
            x (float): coordonnée horizontale dans la fenêtre réelle
            y (float): coordonnée verticale dans la fenêtre réelle
        """
        vx, vy, vw, vh = self._viewport
        scale_x = self._virtual_width  / vw
        scale_y = self._virtual_height / vh
        return (x - vx) * scale_x, (y - vy) * scale_y

    def virtual_to_window(self, x: float, y: float) -> tuple[float, float]:
        """
        Convertit des coordonnées virtuelles en coordonnées réelles

        Args:
            x (float): coordonnée horizontale virtuelle
            y (float): coordonnée verticale virtuelle
        """
        vx, vy, vw, vh = self._viewport
        scale_x = vw / self._virtual_width
        scale_y = vh / self._virtual_height
        return x * scale_x + vx, y * scale_y + vy

    # ======================================== MÉTHODES ========================================
    def clear(self):
        """Efface le contenu de la fenêtre"""
        self._window.clear()

    def set_title(self, title: str):
        """Change le titre de la fenêtre"""
        self._window.set_caption(title)

    def set_fullscreen(self, value: bool):
        """Bascule en plein écran"""
        self._window.set_fullscreen(value)