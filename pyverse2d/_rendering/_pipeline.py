# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..scene import Scene
    from ._window import Window

# ======================================== RENDERER ========================================
class Pipeline:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        virtual_width (int): largeur de l'espace virtuel
        virtual_height (int): hauteur de l'espace virtuel
    """

    def __init__(self, window: Window):
        self._window: Window = window
        self._batch: Batch = Batch()
        self._groups: dict[int, Group] = {}

    # ======================================== GETTERS ========================================
    @property
    def window(self) -> Window:
        """Renvoie la fenêtre OS assignée"""
        return self._window

    @property
    def batch(self) -> Batch:
        """Renvoie le batch global"""
        return self._batch
    
    def get_group(self, z: int = 0) -> Group:
        """
        Renvoie le Group associé au z_order, le crée si inexistant

        Args:
            z (int): z_order du group
        """
        if z not in self._groups:
            self._groups[z] = Group(order=z)
        return self._groups[z]
    
    # ======================================== SETTERS ========================================
    def set_view(self, matrix: Mat4 = None):
        """
        Applique une matrice de vue — identité si None (layers fixed)

        Args:
            matrix(Mat4): matrice de vue, ou None pour annuler la caméra
        """
        self._window.native.view = matrix if matrix is not None else Mat4()

    # ======================================== PIPELINE ========================================
    def begin(self, scene: Scene):
        """
        Configure le contexte de rendu depuis une scene

        Args:
            scene(Scene): scène active à rendre
        """
        screen = self._window.screen

        # NDC
        lx, ly, lw, lh = scene.viewport.resolve(screen.width, screen.height)

        # FrameBuffer
        win_vx, win_vy, win_vw, win_vh = self._window.viewport
        sx = win_vw / screen.width
        sy = win_vh / screen.height

        px = int(win_vx + lx * sx)
        py = int(win_vy + ly * sy)
        pw = int(lw * sx)
        ph = int(lh * sy)

        gl.glViewport(px, py, pw, ph)

    def flush(self):
        """Envoie tout le batch au GPU"""
        self._batch.draw()