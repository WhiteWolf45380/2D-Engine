# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.window.key as _key
import pyglet.window.mouse as _mouse

from typing import TypeAlias

# ======================================== FLAG ========================================
class Key:
    """Table des entrées utilisateur"""
    # Lettres
    A = _key.A
    B = _key.B
    C = _key.C
    D = _key.D
    E = _key.E
    F = _key.F
    G = _key.G
    H = _key.H
    I = _key.I
    J = _key.J
    K = _key.K
    L = _key.L
    M = _key.M
    N = _key.N
    O = _key.O
    P = _key.P
    Q = _key.Q
    R = _key.R
    S = _key.S
    T = _key.T
    U = _key.U
    V = _key.V
    W = _key.W
    X = _key.X
    Y = _key.Y
    Z = _key.Z

    # Chiffres
    NUM_0 = _key._0
    NUM_1 = _key._1
    NUM_2 = _key._2
    NUM_3 = _key._3
    NUM_4 = _key._4
    NUM_5 = _key._5
    NUM_6 = _key._6
    NUM_7 = _key._7
    NUM_8 = _key._8
    NUM_9 = _key._9

    # Navigation
    UP = _key.UP
    DOWN = _key.DOWN
    LEFT = _key.LEFT
    RIGHT = _key.RIGHT

    # Modificateurs
    LSHIFT = _key.LSHIFT
    RSHIFT = _key.RSHIFT
    LCTRL = _key.LCTRL
    RCTRL = _key.RCTRL
    LALT = _key.LALT
    RALT = _key.RALT

    # Actions
    SPACE = _key.SPACE
    ENTER = _key.RETURN
    BACKSPACE = _key.BACKSPACE
    TAB = _key.TAB
    ESCAPE = _key.ESCAPE
    DELETE = _key.DELETE

    # Fonctions
    F1 = _key.F1
    F2 = _key.F2
    F3 = _key.F3
    F4 = _key.F4
    F5 = _key.F5
    F6 = _key.F6
    F7 = _key.F7
    F8 = _key.F8
    F9 = _key.F9
    F10 = _key.F10
    F11 = _key.F11
    F12 = _key.F12

    # Souris
    MOUSELEFT = _mouse.LEFT
    MOUSERIGHT = _mouse.RIGHT
    MOUSEMIDDLE = _mouse.MIDDLE

    # Alias
    Input: TypeAlias = int
    MouseInput: TypeAlias = int
    KeyboardInput: TypeAlias = int

    @staticmethod
    def name(key: Input) -> str:
        return _NAMES.get(key, "Unknown")
    
# ======================================== STR ========================================
_NAMES: dict[Key.Input, str] = {
    # Lettres
    _key.A: "A", _key.B: "B", _key.C: "C", _key.D: "D", _key.E: "E",
    _key.F: "F", _key.G: "G", _key.H: "H", _key.I: "I", _key.J: "J",
    _key.K: "K", _key.L: "L", _key.M: "M", _key.N: "N", _key.O: "O",
    _key.P: "P", _key.Q: "Q", _key.R: "R", _key.S: "S", _key.T: "T",
    _key.U: "U", _key.V: "V", _key.W: "W", _key.X: "X", _key.Y: "Y",
    _key.Z: "Z",

    # Chiffres
    _key._0: "0", _key._1: "1", _key._2: "2", _key._3: "3", _key._4: "4",
    _key._5: "5", _key._6: "6", _key._7: "7", _key._8: "8", _key._9: "9",

    # Navigation
    _key.UP: "Up", _key.DOWN: "Down", _key.LEFT: "Left", _key.RIGHT: "Right",

    # Modificateurs
    _key.LSHIFT: "Left Shift", _key.RSHIFT: "Right Shift",
    _key.LCTRL: "Left Ctrl",  _key.RCTRL: "Right Ctrl",
    _key.LALT: "Left Alt",    _key.RALT: "Right Alt",

    # Actions
    _key.SPACE:     "Space",
    _key.RETURN:    "Enter",
    _key.BACKSPACE: "Backspace",
    _key.TAB:       "Tab",
    _key.ESCAPE:    "Escape",
    _key.DELETE:    "Delete",

    # Fonctions
    _key.F1:  "F1",  _key.F2:  "F2",  _key.F3:  "F3",  _key.F4:  "F4",
    _key.F5:  "F5",  _key.F6:  "F6",  _key.F7:  "F7",  _key.F8:  "F8",
    _key.F9:  "F9",  _key.F10: "F10", _key.F11: "F11", _key.F12: "F12",

    # Souris
    _mouse.LEFT:   "Left Click",
    _mouse.RIGHT:  "Right Click",
    _mouse.MIDDLE: "Middle Click",
}