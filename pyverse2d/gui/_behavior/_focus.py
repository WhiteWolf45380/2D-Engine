# ======================================== IMPORTS ========================================
from ..._internal import expect, CallbackList
from ..._flag import Key
from ..._managers._inputs import _Listener
from ...abc import Behavior
from ...math import Point

from pyverse2d import inputs

from typing import Callable

# ======================================== BEHAVIOR ========================================
class FocusBehavior(Behavior):
    """Behavior gérant la concentration

    Ce ``Behavior`` s'associe automatiquement au ``HoverBehavior`` si le ``Widget`` en possède un.

    Args:
        once: annule la concentration après la première action
    """
    __slots__ = (
        "_once", "_unfocus_on_outside_click", "_unfocus_keys", "_ghost_keys",
        "_on_keydown", "_on_keyup",
        "_listener", "_outside_listeners",
    )
    _ID: str = "focus"

    def __init__(
            self,
            once: bool = False,
            unfocus_on_outside_click: bool = True 
        ):
        # Initialisation du comportement
        super().__init__()

        # Paramètres
        self._once: bool = expect(once, bool)
        self._unfocus_on_outside_click: bool = expect(unfocus_on_outside_click, bool)
        self._unfocus_keys: set[Key.Input] = set(Key.ESCAPE)
        self._ghost_keys: set[Key.Input] = set()

        # Hooks
        self._on_keydown: CallbackList = CallbackList
        self._on_keyup: CallbackList = CallbackList

        # Listeners
        self._listener: _Listener = None
        self._outside_listeners: set[_Listener] = set()

    # ======================================== PROPERTIES ========================================
    @property
    def once(self) -> bool:
        """Fin de concentration dés la première action"""
        return self._once
    
    @once.setter
    def once(self, value: bool) -> None:
        self._once = expect(value, bool)

    @property
    def unfocus_on_outside_click(self) -> bool:
        """Fin de concentration lors du clique en dehors du ``Widget``"""
        return self._unfocus_on_outside_click
    
    @unfocus_on_outside_click.setter
    def unfocus_on_outside_click(self, value: bool):
        if self._unfocus_on_outside_click != value:
            self._unfocus_on_outside_click = expect(value, bool)
            self._apply_outside_click()

    # ======================================== UNFOCUS KEYS ========================================
    def add_unfocus_key(self, key: Key.Input) -> None:
        """Ajoute une clé de fin de concentration
        
        Args:
            key: clé à ajouter
        """
        self._unfocus_keys.add(key)
    
    def remove_unfocus_key(self, key: Key.Input) -> None:
        """Retire une clé de fin de concentration

        Args:
            key: clé à retirer
        """
        self._unfocus_keys.discard(key)

    def clear_unfocus_key(self) -> None:
        """Retire l'ensemble des clés de fin de concentration"""

    # ======================================== GHOST KEYS ========================================

    # ======================================== HOOKS ========================================


    # ======================================== INTERNALS ========================================
    def _is_hovered(self) -> bool:
        """Vérifie si le widget est survolé"""
        if self._owner.hover is None:
            return self._collides(inputs.relative_mouse_position)
        return self._owner.hover.is_hovered()

    def _collides(self, point: Point) -> bool:
        """Vérifie si un point est dans le widget"""
        return self._owner.collidespoint(point)

    def _apply_outside_click(self) -> None:
        """Ajoute ou retire les listeners de clique en dehors du ``Widget``"""
        if self._unfocus_on_outside_click:
            for listener in self._generate_outside_listeners():
                self._outside_listeners.add(listener)

    def _generate_outside_listeners(self) -> tuple[_Listener, ...]:
        """Génère les listeners de clique en dehors du ``Widget``"""
        condition = lambda: not self._is_hovered()
        left = inputs.add_listener(key=Key.MOUSELEFT, callback=self._handle_outside_click, condition=condition)
        middle = inputs.add_listener(key=Key.MOUSEMIDDLE, callback=self._handle_outside_click, condition=condition)
        right = inputs.add_listener(key=Key.MOUSERIGHT, callback=self._handle_outside_click, condition=condition)
        return (left, middle, right)

    def _handle_outside_click(self) -> None:
        pass