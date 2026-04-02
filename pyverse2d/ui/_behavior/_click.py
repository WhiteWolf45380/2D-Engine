# ======================================== IMPORTS ========================================
from ..._flag import Key
from ..._managers._inputs import Listener
from ..._rendering import Pipeline, RenderContext
from ...abc import Behavior, Widget

from pyverse2d import inputs

from typing import Callable, Any

# ======================================== BEHAVIOR ========================================
class ClickBehavior(Behavior):
    """Behavior gérant le clique

    La détection ne peut se faire que si le widget possède un ``HoverBehavior``.
    """
    __slots__ = ("_down_listeners", "_up_listeners")
    _ID: str = "click"

    def __init__(self):
        # Initialisation du comportement
        super().__init__()

        # Actions
        self._down_listeners: dict[str, Listener] = {}
        self._up_listeners: dict[str, Listener] = {}

    def add(
        self,
        name: str = None,
        key: Key.MouseInput = Key.MOUSELEFT,
        callback: Callable = None,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        when_up: Callable = None,
        condition: Callable = None,
        once: bool = False,
        repeat: bool = False,
        priority: int = 0,
        give_key: bool = False,
    ) -> None:
        """Ajoute une action lors du clique sur le widget

        Args:
            name: identifant associé à l'action
            key: ``MouseInput`` à détecter
            callback: ``fonction`` à appeler
            args: arguments à passer à la fonction
            kwargs: arguments nommés à passer à la fonction
            when_up: ``fonction`` à appeler lors du relâchement
            condition: ``fonction`` de confirmation lors du clique
            once: supprime le listener après éxécution
            repeat: répète l'action tant que le clique est maintenu
            priority: priorité de l'action
            give_key: passe un argument ``key`` à la fonction
        """
        if name is None:
            name = f"click_{len(self._down_listeners)}"
        elif name in self._down_listeners:
            raise ValueError(f"This bhavior already has a Listener {name}")

        down_listener: Listener = inputs.add_listener(
            key = key,
            callback = callback,
            args = args,
            kwargs = kwargs,
            condition = lambda: condition() and self._is_hovered() if condition is not None else self._is_hovered(),
            once = once,
            repeat = repeat,
            priority = priority,
            give_key = give_key,
        )
        self._down_listeners[name] = down_listener

        if when_up:
            up_listener: Listener = inputs.add_listener(
                key = key,
                up = True,
            )
            self._up_listeners[name] = up_listener

    # ======================================== LISTENERS ========================================
    def remove(self, name: str) -> None:
        """Supprime une action

        Args:
            name: identifiant de l'action à supprimer
        """
        if name not in self._down_listeners:
            raise ValueError(f"This behavior doesn't have a Listener {name}")
        
        inputs.remove_listener(self._down_listeners[name])
        del self._down_listeners[name]

        if name in self._up_listeners:
            inputs.remove_listener(self._up_listeners[name])
            del self._up_listeners[name]
    
    def remove_with_filters(self, key: Key.MouseInput = None, callback: Callable = None) -> None:
        """Supprime les actions correspondant aux filtres

        Args:
            key: ``MouseInput`` à filtrer
            callback: ``fonction`` à filtrer
        """
        for name, listener in self._down_listeners.items():
            if (key is not None and listener.key != key) or (callback is not None and listener.callback != callback):
                continue
            self.remove(name)

    def remove_all(self) -> None:
        """Supprime toutes les actions"""
        for name in list(self._down_listeners.keys()):
            self.remove(name)

    # ======================================== HOOKS ========================================
    def _attach(self, widget: Widget) -> None:
        """Hook d'attachement
        
        Args:
            widget: composant UI maître
        """
        pass

    def _detach(self) -> None:
        """Hook de détachement"""
        self.remove_all()

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        pass

    # ======================================== INTERNALS ========================================
    def _is_hovered(self) -> bool:
        """Vérifie si le widget est survolé"""
        return self._owner.hover is not None and self._owner.hover._is_hovered()