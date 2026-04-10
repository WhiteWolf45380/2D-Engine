# ======================================== IMPORTS ========================================
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# ======================================== RENDER TOOLS ========================================
def center_vertices(vertices: NDArray[np.float32]) -> NDArray[np.float32]:
    """Recentre des vertices autour de ``(0, 0)``

    Args:
        vertices: ``(N, 2)`` points du polygone
    """
    v = np.asarray(vertices, dtype=np.float32)
    if len(v) == 0:
        return v

    center = v.mean(axis=0)
    return v - center


def order_ccw(vertices: NDArray[np.float32]) -> NDArray[np.float32]:
    """Ordonne des vertices en sens anti-horaire (CCW)

    Args:
        vertices: ``(N, 2)`` points du polygone
    """
    v = np.asarray(vertices, dtype=np.float32)
    if len(v) < 3:
        return v

    # centre du polygone
    center = v.mean(axis=0)

    # angle polaire autour du centre
    angles = np.arctan2(v[:, 1] - center[1], v[:, 0] - center[0])

    order = np.argsort(angles)
    return v[order]


def is_convex(vertices: NDArray[np.float32]) -> bool:
    v = np.asarray(vertices, dtype=np.float32)
    n = len(v)
    if n < 3:
        return False

    a = v
    b = np.roll(v, -1, axis=0)
    c = np.roll(v, -2, axis=0)

    cross = (b[:,0]-a[:,0]) * (c[:,1]-a[:,1]) - (b[:,1]-a[:,1]) * (c[:,0]-a[:,0])

    non_zero = cross[np.abs(cross) > 1e-8]
    if len(non_zero) == 0:
        return True

    return np.all(non_zero > 0) or np.all(non_zero < 0)