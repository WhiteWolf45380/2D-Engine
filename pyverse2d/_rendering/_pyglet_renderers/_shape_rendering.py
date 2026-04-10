# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...typing import BorderAlign
from ...abc import Shape, VertexShape
from ...shape import Capsule, Circle, Ellipse, RoundedRect
from ...asset import Color
from .._pipeline import Pipeline

import pyglet
import pyglet.gl
from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram

import math
import numpy as np

# ======================================== CONSTANTS ========================================
_UNSET = object()

# Tous les paramètres qui influencent la géométrie monde
_TRANSFORM_DEPS = frozenset({"x", "y", "anchor_x", "anchor_y", "scale", "rotation"})

_CIRCLE_BORDER_SEGMENTS       = 64
_ELLIPSE_BORDER_SEGMENTS      = 64
_CAPSULE_BORDER_SEGMENTS      = 32
_ROUNDED_RECT_BORDER_SEGMENTS = 16


# ======================================== PUBLIC ========================================
class PygletShapeRenderer:
    """
    Renderer pyglet unifié pour une shape géométrique.
    Le remplissage utilise le Mesh de la shape (world_vertices + get_indexes),
    la bordure utilise un triangle strip calculé sur le contour local.

    Args:
        shape:        shape à rendre
        x:            position horizontale monde
        y:            position verticale monde
        anchor_x:     ancre relative locale horizontale [0, 1]
        anchor_y:     ancre relative locale verticale   [0, 1]
        scale:        facteur d'échelle uniforme
        rotation:     rotation en degrés (sens trigonométrique)
        filling:      activer le remplissage
        color:        couleur de remplissage
        border_width: épaisseur de la bordure en pixels
        border_align: alignement de la bordure ("center" | "in" | "out")
        border_color: couleur de la bordure
        opacity:      opacité globale [0.0, 1.0]
        z:            z-order
        pipeline:     pipeline de rendu
    """
    __slots__ = (
        "_shape",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_scale", "_rotation",
        "_filling", "_color",
        "_border_width", "_border_align", "_border_color",
        "_opacity", "_z", "_pipeline",
        "_fill", "_border",
    )

    def __init__(
        self,
        shape: Shape,
        x: float = 0.0,
        y: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
        scale: float = 1.0,
        rotation: float = 0.0,
        filling: bool = True,
        color: Color = None,
        border_width: int = 0,
        border_align: BorderAlign = "center",
        border_color: Color = None,
        opacity: float = 1.0,
        z: int = 0,
        pipeline: Pipeline = None,
    ):
        self._shape        = shape
        self._x            = x
        self._y            = y
        self._anchor_x     = anchor_x
        self._anchor_y     = anchor_y
        self._scale        = scale
        self._rotation     = rotation
        self._filling      = filling
        self._color        = color
        self._border_width = border_width
        self._border_align = border_align
        self._border_color = border_color
        self._opacity      = opacity
        self._z            = z
        self._pipeline     = pipeline
        self._fill: _FillRenderer   = None
        self._border: _BorderRenderer = None
        self._build()

    # ======================================== INTERNALS ========================================
    def _build(self) -> None:
        """Construit les sous-renderers fill et border"""
        if self._filling and self._color is not None:
            self._fill = _FillRenderer(self)
        if self._border_width > 0 and self._border_color is not None:
            self._border = _BorderRenderer(self)

    # ======================================== GETTERS ========================================
    @property
    def shape(self)        -> Shape:       return self._shape
    @property
    def position(self)     -> tuple:       return (self._x, self._y)
    @property
    def x(self)            -> float:       return self._x
    @property
    def y(self)            -> float:       return self._y
    @property
    def anchor_x(self)     -> float:       return self._anchor_x
    @property
    def anchor_y(self)     -> float:       return self._anchor_y
    @property
    def scale(self)        -> float:       return self._scale
    @property
    def rotation(self)     -> float:       return self._rotation
    @property
    def filling(self)      -> bool:        return self._filling
    @property
    def color(self)        -> Color:       return self._color
    @property
    def border_width(self) -> int:         return int(self._border_width)
    @property
    def border_align(self) -> BorderAlign: return self._border_align
    @property
    def border_color(self) -> Color:       return self._border_color
    @property
    def opacity(self)      -> float:       return self._opacity
    @property
    def z(self)            -> int:         return self._z
    @property
    def pipeline(self)     -> Pipeline:    return self._pipeline

    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        if self._fill:   return self._fill.visible
        if self._border: return self._border.visible
        return False

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou désactive la visibilité"""
        if self._fill:   self._fill.visible   = value
        if self._border: self._border.visible = value

    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité effective"""
        return self.visible and (
            (self._filling      and self._color        is not None)
            or (self._border_width > 0 and self._border_color is not None)
        )

    # ======================================== LIFE CYCLE ========================================
    def update(self, **kwargs) -> None:
        """
        Met à jour le renderer.

        Args:
            shape:        nouvelle forme
            x:            position horizontale
            y:            position verticale
            anchor_x:     ancre horizontale
            anchor_y:     ancre verticale
            scale:        facteur de redimensionnement
            rotation:     rotation en degrés
            filling:      remplissage activé
            color:        couleur de remplissage
            border_width: épaisseur de bordure
            border_align: alignement de la bordure
            border_color: couleur de bordure
            opacity:      opacité
            z:            z-order
            pipeline:     pipeline de rendu
        """
        changes: set[str] = set()
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            changes.add(key)

        if not changes:
            return

        # --- Remplissage ---
        if self._filling:
            if self._fill is not None:
                self._fill.update(self, changes)
            elif self._color is not None:
                self._fill = _FillRenderer(self)
        elif self._fill is not None:
            self._fill.delete()
            self._fill = None

        # --- Bordure ---
        if self._border_width > 0:
            if self._border is not None:
                self._border.update(self, changes)
            elif self._border_color is not None:
                self._border = _BorderRenderer(self)
        elif self._border is not None:
            self._border.delete()
            self._border = None

    def delete(self) -> None:
        """Libère toutes les ressources pyglet"""
        if self._fill:
            self._fill.delete()
            self._fill = None
        if self._border:
            self._border.delete()
            self._border = None


# ======================================== FILL RENDERER ========================================
class _FillRenderer:
    """
    Remplissage mesh-based, shape-agnostic.

    Stratégie GPU :
      - Les vertices monde sont calculés CPU à chaque transform (upload partiel).
      - Les indexes sont constants : uploadés une seule fois à la construction.
      - Si la géométrie locale change (scale shape, etc.), un rebuild complet est requis.

    Note : pour aller plus loin, on pourrait garder les vertices en local space sur le GPU
    et passer le transform en uniform (nécessite un shader custom).
    """
    __slots__ = ("_vlist", "_n", "_program", "_visible", "_stored_colors")

    # Shader partagé entre toutes les instances (initialisé paresseusement)
    _PROGRAM: ShaderProgram = None

    @classmethod
    def _get_program(cls) -> ShaderProgram:
        if cls._PROGRAM is None:
            # get_default_shader() : shader 2D intégré de pyglet
            # Attributs attendus : position ('f', vec2) + colors ('Bn', RGBA bytes)
            cls._PROGRAM = pyglet.shapes.get_default_shader()
        return cls._PROGRAM

    def __init__(self, psr: PygletShapeRenderer):
        self._vlist          = None
        self._n: int         = 0
        self._program        = self._get_program()
        self._visible: bool  = True
        self._stored_colors  = None
        self._build(psr)

    # ======================================== BUILD ========================================
    def _build(self, psr: PygletShapeRenderer) -> None:
        """(Re)construit le vertex_list_indexed depuis le Mesh de la shape"""
        if self._vlist is not None:
            self._vlist.delete()

        vertices = psr.shape.world_vertices(
            psr.x, psr.y, psr.scale, psr.rotation,
            psr.anchor_x, psr.anchor_y,
        )
        indexes  = psr.shape.get_indexes()
        self._n  = len(vertices)

        r, g, b, a = psr.color.rgba8
        a = int(a * psr.opacity)

        self._vlist = self._program.vertex_list_indexed(
            self._n,
            pyglet.gl.GL_TRIANGLES,
            indexes.flatten().tolist(),         # indexes : constants, uploadés une fois
            psr.pipeline.batch,
            psr.pipeline.get_group(z=psr.z),
            position = ('f',  vertices.flatten().tolist()),
            colors   = ('Bn', (r, g, b, a) * self._n),
        )

    # ======================================== GETTERS ========================================
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._visible

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou masque via alpha (vertex_list n'a pas de .visible natif)"""
        if value == self._visible:
            return
        self._visible = value
        if value:
            self._vlist.colors[:] = self._stored_colors
            self._stored_colors = None
        else:
            self._stored_colors = list(self._vlist.colors[:])
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: set[str]) -> None:
        """Applique les changements de manière incrémentale"""

        # Rebuild complet si le batch ou le z-order changent
        if "z" in changes or "pipeline" in changes:
            self._build(psr)
            return

        # Upload partiel des positions si le transform a bougé
        if changes & _TRANSFORM_DEPS:
            vertices = psr.shape.world_vertices(
                psr.x, psr.y, psr.scale, psr.rotation,
                psr.anchor_x, psr.anchor_y,
            )
            self._vlist.position[:] = vertices.flatten().tolist()

        # Mise à jour de la couleur/opacité
        if "color" in changes or "opacity" in changes:
            r, g, b, a = psr.color.rgba8
            a = int(a * psr.opacity)
            self._vlist.colors[:] = (r, g, b, a) * self._n

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None


# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """
    Bordure triangle-strip d'une shape.
    Le contour local est calculé une seule fois à la construction ;
    seul le transform monde est recalculé lors des mises à jour.
    """
    __slots__ = ("_vlist", "_n", "_program", "_batch", "_group",
                 "_local_contour", "_visible", "_stored_colors")

    _PROGRAM: ShaderProgram = None
    _BASE_GROUP: Group      = None

    @classmethod
    def _get_program(cls) -> ShaderProgram:
        if cls._PROGRAM is None:
            cls._PROGRAM = pyglet.shapes.get_default_shader()
        return cls._PROGRAM

    @classmethod
    def _get_base_group(cls) -> Group:
        if cls._BASE_GROUP is None:
            cls._BASE_GROUP = pyglet.graphics.ShaderGroup(cls._get_program(), order=1)
        return cls._BASE_GROUP

    def __init__(self, psr: PygletShapeRenderer):
        self._vlist          = None
        self._n: int         = 0
        self._program        = self._get_program()
        self._batch          = None
        self._group          = None
        self._visible: bool  = True
        self._stored_colors  = None
        self._local_contour  = _local_contour(psr.shape)   # calculé une seule fois
        self._build(psr)

    # ======================================== BUILD ========================================
    def _build(self, psr: PygletShapeRenderer) -> None:
        """(Re)construit le vertex_list du triangle strip"""
        if self._vlist is not None:
            self._vlist.delete()

        self._batch = psr.pipeline.batch
        self._group = pyglet.graphics.Group(order=psr.z, parent=self._get_base_group())

        strip    = _world_strip(self._local_contour, psr)
        self._n  = len(strip)
        flat     = strip.flatten().tolist()

        r, g, b, a = psr.border_color.rgba8
        a = int(a * psr.opacity)

        self._vlist = self._program.vertex_list(
            self._n,
            pyglet.gl.GL_TRIANGLE_STRIP,
            self._batch,
            self._group,
            position = ('f',  flat),
            colors   = ('Bn', (r, g, b, a) * self._n),
        )

    def _refresh_vertices(self, psr: PygletShapeRenderer) -> None:
        """Upload partiel des positions (strip recalculé, indexes inchangés)"""
        strip = _world_strip(self._local_contour, psr)
        self._vlist.position[:] = strip.flatten().tolist()

    # ======================================== GETTERS ========================================
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._visible

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou masque via alpha"""
        if value == self._visible:
            return
        self._visible = value
        if value:
            self._vlist.colors[:] = self._stored_colors
            self._stored_colors = None
        else:
            self._stored_colors = list(self._vlist.colors[:])
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: set[str]) -> None:
        """Applique les changements de manière incrémentale"""

        # Rebuild complet si le batch ou le z-order changent
        if "z" in changes or "pipeline" in changes:
            self._build(psr)
            return

        # Upload partiel des positions si la géométrie monde a changé
        if changes & (_TRANSFORM_DEPS | {"border_width", "border_align"}):
            self._refresh_vertices(psr)

        # Mise à jour de la couleur/opacité
        if "border_color" in changes or "opacity" in changes:
            r, g, b, a = psr.border_color.rgba8
            a = int(a * psr.opacity)
            self._vlist.colors[:] = (r, g, b, a) * self._n

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None


# ======================================== BORDER HELPERS ========================================
def _local_contour(shape: Shape) -> np.ndarray:
    """
    Génère le contour local polygonal d'une shape pour la bordure.
    Appelé une seule fois à la construction du BorderRenderer.
    """
    if isinstance(shape, VertexShape):
        return np.array(shape.vertices, dtype=np.float32)

    elif isinstance(shape, Circle):
        angles = np.linspace(0, 2 * np.pi, _CIRCLE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((
            np.cos(angles) * shape.radius,
            np.sin(angles) * shape.radius,
        )).astype(np.float32)

    elif isinstance(shape, Ellipse):
        angles = np.linspace(0, 2 * np.pi, _ELLIPSE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((
            np.cos(angles) * shape.rx,
            np.sin(angles) * shape.ry,
        )).astype(np.float32)

    elif isinstance(shape, Capsule):
        return _capsule_local_contour(shape)

    elif isinstance(shape, RoundedRect):
        return _rounded_rect_local_contour(shape)

    raise TypeError(f"Shape non supportée pour la bordure : {type(shape)}")


def _capsule_local_contour(shape: Capsule) -> np.ndarray:
    """Contour local d'une capsule"""
    half_len = shape.spine / 2.0
    r        = shape.radius
    half     = _CAPSULE_BORDER_SEGMENTS // 2

    angles_b = np.linspace(0,      np.pi, half + 1)
    angles_a = np.linspace(np.pi, 2 * np.pi, half + 1)

    pts_b = np.column_stack((r * np.cos(angles_b),  half_len + r * np.sin(angles_b)))
    pts_a = np.column_stack((r * np.cos(angles_a), -half_len + r * np.sin(angles_a)))

    return np.vstack((pts_b, pts_a)).astype(np.float32)


def _rounded_rect_local_contour(shape: RoundedRect) -> np.ndarray:
    """Contour local d'un rectangle arrondi"""
    r  = shape.radius
    hx = shape.inner_width  * 0.5
    hy = shape.inner_height * 0.5

    seg = max(_ROUNDED_RECT_BORDER_SEGMENTS, int(r * 0.75))
    corners = [
        ( hx,  hy, 0.0,           np.pi * 0.5),
        (-hx,  hy, np.pi * 0.5,   np.pi      ),
        (-hx, -hy, np.pi,         np.pi * 1.5),
        ( hx, -hy, np.pi * 1.5,   np.pi * 2.0),
    ]

    pts = []
    for cx, cy, a_start, a_end in corners:
        angles = np.linspace(a_start, a_end, seg, endpoint=False)
        arc = np.column_stack((cx + r * np.cos(angles), cy + r * np.sin(angles)))
        pts.append(arc)

    return np.vstack(pts).astype(np.float32)


def _world_strip(local_contour: np.ndarray, psr: PygletShapeRenderer) -> np.ndarray:
    """Applique le transform monde au contour local puis génère le triangle strip"""
    world = _apply_transform(local_contour, psr)
    return _build_strip(world, psr.border_width, psr.border_align)


def _apply_transform(pts: np.ndarray, psr: PygletShapeRenderer) -> np.ndarray:
    """
    Transform local → monde : scale + rotation + translation avec anchor.
    Miroir exact de Shape.world_vertices() pour garantir l'alignement fill / border.

        world = local * scale @ R + ([x, y] - anchor_local)
    """
    xmin, ymin, xmax, ymax = psr.shape.get_bounding_box()
    anchor = np.array([
        xmin + psr.anchor_x * (xmax - xmin),
        ymin + psr.anchor_y * (ymax - ymin),
    ], dtype=np.float32)
    translation = np.array([psr.x, psr.y], dtype=np.float32) - anchor

    rad   = math.radians(psr.rotation)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    R = np.array([[cos_r, -sin_r],
                  [sin_r,  cos_r]], dtype=np.float32)

    return (pts * psr.scale) @ R + translation


def _build_strip(contour: np.ndarray, width: float, align: str = "center") -> np.ndarray:
    """Génère un triangle strip (N+1)*2 points autour d'un contour fermé"""
    n        = len(contour)
    prev_pts = contour[(np.arange(n) - 1) % n]
    next_pts = contour[(np.arange(n) + 1) % n]

    def edge_normals(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        d = b - a
        lengths = np.linalg.norm(d, axis=1, keepdims=True)
        lengths = np.where(lengths == 0, 1, lengths)
        d /= lengths
        return np.column_stack((-d[:, 1], d[:, 0]))

    n1   = edge_normals(prev_pts, contour)
    n2   = edge_normals(contour, next_pts)
    miter = n1 + n2

    miter_len = np.linalg.norm(miter, axis=1, keepdims=True)
    miter_len = np.where(miter_len == 0, 1, miter_len)
    miter /= miter_len

    dot = np.einsum('ij,ij->i', n1, miter).reshape(-1, 1)
    dot = np.where(np.abs(dot) < 0.01, 0.01, dot)

    if align == "center":
        half       = width / 2.0
        miter_dist = np.clip(half / dot, -width * 3, width * 3)
        outer      = contour + miter * miter_dist
        inner      = contour - miter * miter_dist
    elif align == "in":
        miter_dist = np.clip(width / dot, -width * 3, width * 3)
        outer      = contour + miter * miter_dist
        inner      = contour
    elif align == "out":
        miter_dist = np.clip(width / dot, -width * 3, width * 3)
        outer      = contour
        inner      = contour - miter * miter_dist

    strip          = np.empty(((n + 1) * 2, 2), dtype=np.float32)
    strip[0::2][:n] = outer
    strip[1::2][:n] = inner
    strip[-2]        = outer[0]
    strip[-1]        = inner[0]

    return strip