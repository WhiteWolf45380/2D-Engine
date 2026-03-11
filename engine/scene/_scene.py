# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from ._layer import Layer

# ======================================== OBJECT ========================================
class Scene:
    """Contient et orchestre un ensemble de layers ordonnés"""
    def __init__(self):
        self._layers: list[Layer] = []

    # ======================================== LIFE CYCLE ========================================
    def on_start(self):
        for layer in self._layers:
            layer.on_start()

    def on_stop(self):
        for layer in self._layers:
            layer.on_stop()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        for layer in self._layers:
            layer.update(dt)

    def draw(self):
        for layer in self._layers:
            layer.draw()
    
    # ======================================== LAYERS ========================================
    def add_layer(self, layer: Layer) -> Scene:
        self._layers.append(expect(layer, Layer))
        return self

    def remove_layer(self, layer: Layer) -> Scene:
        self._layers.remove(expect(layer, Layer))
        return self