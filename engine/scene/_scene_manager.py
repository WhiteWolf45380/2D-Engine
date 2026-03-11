# ======================================== IMPORTS ========================================
from .._internal import expect

from ._scene import Scene
from ._stack_mode import StackMode

# ======================================== MANAGER ========================================
class SceneManager:
    """Gère les transitions et l'empilement des scenes"""
    def __init__(self):
        self._stack: list[Scene] = []

    # ======================================== GETTERS ========================================
    @property
    def current(self) -> Scene | None:
        """Renvoie la scene active"""
        return self._stack[-1] if self._stack else None

    # ======================================== TRANSITIONS ========================================
    def load(self, scene: Scene):
        """Remplace toute la stack par une scene"""
        for s in reversed(self._stack):
            s.on_stop()
        self._stack.clear()
        self._stack.append(expect(scene, Scene))
        scene.on_start()

    def switch(self, scene: Scene):
        """Remplace la scene active par une autre"""
        if self._stack:
            self._stack[-1].on_stop()
            self._stack.pop()
        self._stack.append(expect(scene, Scene))
        scene.on_start()

    def push(self, scene: Scene, mode: StackMode = StackMode.PAUSE):
        """Ajoute une scene active"""
        if self._stack:
            below = self._stack[-1]
            if mode == StackMode.PAUSE:
                below.on_stop()
            elif mode == StackMode.SUSPEND:
                below.suspend()
            self._stack.append((scene, mode))
            scene.on_start()

    def pop(self):
        """Dépile la scene active et reprend la précédente"""
        if self._stack:
            self._stack[-1].on_stop()
            self._stack.pop()
        if self._stack:
            self._stack[-1].on_start()

    # ======================================== LOOP ========================================
    def update(self, dt):
        """Actualisation des scenes"""
        for scene, mode in self._stack:
            if mode != StackMode.PAUSE:
                scene.update(dt)

    def draw(self):
        """Affichage des scenes"""
        for scene, _ in self._stack:
            scene.draw()