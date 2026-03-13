# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._rendering._pipeline import Pipeline
from .._flag import StackMode, SceneState, CameraMode
from ..math import Point
from ..abc import Layer

from ._camera import Camera
from ._viewport import Viewport

import bisect

# ======================================== SCENE ========================================
class Scene:
    """
    Orchestre un ensemble de layers ordonnés par z_order

    Args:
        camera(Camera): caméra de la scene
        viewport(Viewport): viewport de la scene
        stack_mode(StackMode): mode d'empilement par rapport aux autres scenes
    """
    def __init__(self, camera: Camera = None, viewport: Viewport = None, stack_mode: StackMode = StackMode.OVERLAY):
        self._layers: list[Layer] = []
        self._z_orders: list[int] = []
        self._camera: Camera = expect(camera, Camera) if camera else Camera(Point(0, 0))
        self._viewport: Viewport = expect(viewport, Viewport) if viewport else Viewport()
        self._stack_mode: StackMode = expect(stack_mode, StackMode)
        self._state: SceneState = SceneState.SLEEPING

    # ======================================== GETTERS ========================================
    @property
    def camera(self) -> Camera:
        """Renvoie la caméra de la scene"""
        return self._camera

    @property
    def viewport(self) -> Viewport:
        """Renvoie le viewport de la scene"""
        return self._viewport
    
    @property
    def stack_mode(self) -> StackMode:
        """Renvoie le mode d'empilement"""
        return self._stack_mode
    
    @property
    def state(self) -> SceneState:
        """Renvoie l'état de la scène"""
        return self._state

    # ======================================== SETTERS ========================================
    def set_camera(self, camera: Camera):
        """
        Fixe la caméra de la scene

        Args:
            camera(Camera): caméra à utiliser
        """
        self._camera = expect(camera, Camera)

    def set_viewport(self, viewport: Viewport):
        """
        Fixe le viewport de la scene

        Args:
            viewport(Viewport): viewport à utiliser
        """
        self._viewport = expect(viewport, Viewport)
    
    def set_stack_mode(self, stack_mode: StackMode):
        """
        Fixe le mode d'empilement

        Args:
            stackmode(StackMode): mode d'empilement de la scène
        """
        self._stack_mode = expect(stack_mode, StackMode)
    
    def set_state(self, state: SceneState):
        """
        Fixe l'état de la scène

        Args:
            state(SceneState): état de la scène
        """
        self._state = expect(state, SceneState)

    # ======================================== LAYERS ========================================
    def add_layer(self, layer: Layer, z: int = 0) -> Scene:
        """
        Ajoute un layer à la scene

        Args:
            layer (Layer): layer à ajouter
            z (int): ordre de rendu
        """
        expect(layer, Layer)
        i = bisect.bisect_right(self._z_orders, z)
        self._z_orders.insert(i, z)
        self._layers.insert(i, layer)
        return self

    def remove_layer(self, layer: Layer) -> Scene:
        """
        Supprime un layer de la scene

        Args:
            layer (Layer): layer à supprimer
        """
        i = self._layers.index(expect(layer, Layer))
        self._layers.pop(i)
        self._z_orders.pop(i)
        return self

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self):
        """Démarre tous les layers"""
        for layer in self._layers:
            layer.on_start()

    def on_stop(self):
        """Arrête tous les layers"""
        for layer in self._layers:
            layer.on_stop()

    def suspend(self):
        """Suspend tous les layers"""
        for layer in self._layers:
            layer.on_stop()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """
        Met à jour tous les layers

        Args:
            dt (float): delta time
        """
        for layer in self._layers:
            layer.update(dt)

    def draw(self, pipeline: Pipeline):
        """
        Dessine tous les layers dans l'ordre de z_order

        Args:
            pipeline: pipeline à utiliser pour le rendu
        """
        pipeline.begin(self)
        camera_view = self.camera.view_matrix()
        camera_zoom = self.camera.zoom_matrix()
        for layer in self._layers:
            if layer.camera_mode is CameraMode.WORLD: pipeline.set_view(camera_view)        # WORLD
            elif layer.camera_mode is CameraMode.ZOOM: pipeline.set_view(camera_zoom)       # ZOOM
            else: pipeline.set_view(None)                                                   # SCREEN
            layer.draw(pipeline)
        pipeline.flush()