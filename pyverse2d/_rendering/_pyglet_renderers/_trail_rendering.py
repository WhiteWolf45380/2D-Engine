# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...asset import Image, Color
from ..._rendering import Pipeline
from ...math.easing import EasingFunc

from collections import deque
from typing import ClassVar

import pyglet
import pyglet.resource
import os
import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.gl import (
    glBindTexture, glTexParameteri,
    GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE,
)

import math

# ======================================== SHADERS ========================================
_VERT_COLOR = """
#version 330 core
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec4 in_color;
out vec4 v_color;
uniform mat4 u_mvp;
void main() {
    gl_Position = u_mvp * vec4(in_position, 0.0, 1.0);
    v_color = in_color;
}
"""

_FRAG_COLOR = """
#version 330 core
in vec4 v_color;
out vec4 out_color;
void main() {
    out_color = v_color;
}
"""

_VERT_TEX = """
#version 330 core
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_uv;
layout(location = 2) in float in_alpha;
out vec2 v_uv;
out float v_alpha;
uniform mat4 u_mvp;
void main() {
    gl_Position = u_mvp * vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
    v_alpha = in_alpha;
}
"""

_FRAG_TEX = """
#version 330 core
uniform sampler2D u_texture;
uniform vec3 u_tint;
in vec2 v_uv;
in float v_alpha;
out vec4 out_color;
void main() {
    vec4 tex = texture(u_texture, v_uv);
    out_color = vec4(tex.rgb * u_tint, tex.a * v_alpha);
}
"""

# ======================================== RENDERER ========================================
class PygletTrailRenderer:
    """Renderer bas niveau pour un ``TrailRenderer``

    Args:
        max_points: bucket de points
        image: texture répétée *(couleur unie si None)*
    """
    __slots__ = (
        "_vao", "_vbo",
        "_textured", "_texture_id",
        "_max_verts", "_vertex_count",
        "_floats_per_vert",
        "_visible",
    )

    _color_program: ClassVar[ShaderProgram | None] = None
    _tex_program: ClassVar[ShaderProgram | None] = None
    _texture_cache: ClassVar[dict[str, int]] = {}

    @classmethod
    def _get_color_program(cls) -> ShaderProgram:
        if cls._color_program is None:
            cls._color_program = ShaderProgram(
                Shader(_VERT_COLOR, 'vertex'),
                Shader(_FRAG_COLOR, 'fragment'),
            )
        return cls._color_program

    @classmethod
    def _get_tex_program(cls) -> ShaderProgram:
        if cls._tex_program is None:
            cls._tex_program = ShaderProgram(
                Shader(_VERT_TEX, 'vertex'),
                Shader(_FRAG_TEX, 'fragment'),
            )
        return cls._tex_program

    @classmethod
    def _load_texture(cls, path: str) -> int:
        """Charge (ou retourne depuis le cache) une texture GL depuis un chemin

        Args:
            path: chemin du fichier image

        Returns:
            identifiant GL de la texture
        """
        if path in cls._texture_cache:
            return cls._texture_cache[path]

        directory = os.path.dirname(os.path.abspath(path))
        if directory not in pyglet.resource.path:
            pyglet.resource.path.append(directory)
            pyglet.resource.reindex()

        try:
            raw = pyglet.resource.image(os.path.basename(path), atlas=False)
            tex_id = raw.get_texture().id
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            cls._texture_cache[path] = tex_id
            return tex_id
        except pyglet.resource.ResourceNotFoundException:
            print(f"[PygletTrailRenderer] Cannot load texture: {path}")
            cls._texture_cache[path] = 0
            return 0

    def __init__(self, max_points: int, image: Image | None) -> None:
        self._textured: bool = image is not None
        self._texture_id: int = self._load_texture(image.path) if image is not None else 0
        self._vertex_count: int = 0
        self._visible: bool = True
        self._floats_per_vert: int = 5 if self._textured else 6
        self._max_verts: int = max_points * 2

        self._vao = (gl.GLuint * 1)()
        self._vbo = (gl.GLuint * 1)()
        gl.glGenVertexArrays(1, self._vao)
        gl.glGenBuffers(1, self._vbo)
        gl.glBindVertexArray(self._vao[0])
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo[0])

        stride = self._floats_per_vert * 4
        total_bytes = self._max_verts * stride
        gl.glBufferData(gl.GL_ARRAY_BUFFER, total_bytes, None, gl.GL_DYNAMIC_DRAW)

        if self._textured:
            # x, y, u, v, alpha
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, 0)
            gl.glEnableVertexAttribArray(1)
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, 8)
            gl.glEnableVertexAttribArray(2)
            gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, 16)
        else:
            # x, y, r, g, b, a
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, 0)
            gl.glEnableVertexAttribArray(1)
            gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, gl.GL_FALSE, stride, 8)

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    # ======================================== UPDATE ========================================
    def update(
        self,
        points: deque[tuple[float, float, float]],
        width: float,
        duration: float,
        color: Color,
        opacity: float,
        width_easing: EasingFunc | None,
        opacity_easing: EasingFunc | None,
        smooth: bool,
    ) -> None:
        """Reconstruit le mesh depuis le buffer de points et uploade au GPU

        Args:
            points: buffer de points *(x, y, age)*
            width: largeur maximale en unités monde
            duration: durée de vie des points en secondes
            color: couleur RGBA *(mode couleur unie)*
            opacity: opacité globale
            width_easing: courbe de largeur *(None = fixe)*
            opacity_easing: courbe d'opacité *(None = fixe)*
            smooth: lissage Catmull-Rom avec normales analytiques
        """
        raw_pts = list(points)
        n_raw = len(raw_pts)

        if n_raw < 2:
            self._vertex_count = 0
            return

        # Lissage Catmull-Rom avec normales analytiques
        smoothed_mode = False
        if smooth and n_raw >= 4:
            smoothed_mode = True
            steps = 10
            pt_list: list = []
            for i in range(n_raw - 1):
                p0 = raw_pts[max(i - 1, 0)]
                p1 = raw_pts[i]
                p2 = raw_pts[i + 1]
                p3 = raw_pts[min(i + 2, n_raw - 1)]
                for s in range(steps):
                    pt_list.append(_catmull_rom(p0, p1, p2, p3, s / steps))
            # Dernier point avec tangente finale
            pt_list.append(_catmull_rom(
                raw_pts[-4], raw_pts[-3], raw_pts[-2], raw_pts[-1], 1.0,
            ))
        else:
            pt_list = raw_pts

        n = len(pt_list)

        # Longueurs cumulées pour UV
        lengths: list[float] = [0.0]
        for i in range(1, n):
            ax, ay = pt_list[i-1][0], pt_list[i-1][1]
            bx, by = pt_list[i][0], pt_list[i][1]
            dx, dy = bx - ax, by - ay
            lengths.append(lengths[-1] + math.sqrt(dx*dx + dy*dy))
        total_length = lengths[-1] if lengths[-1] > 1e-6 else 1.0

        # Génération du mesh
        cr, cg, cb = color.rgb
        fpv = self._floats_per_vert
        buf = (gl.GLfloat * (self._max_verts * fpv))()
        vi = 0

        for i, pt in enumerate(pt_list):
            if vi >= self._max_verts:
                break

            px, py, age = pt[0], pt[1], pt[2]

            # Normale : analytique si smooth, moyennée sinon
            if smoothed_mode:
                nx, ny = pt[3], pt[4]
            else:
                nx, ny = _normal_at(pt_list, i)

            # Largeur
            t_life = max(0.0, min(1.0, 1.0 - age / duration))
            hw = width * 0.5 * (width_easing(t_life) if width_easing else 1.0)

            # Extrusion en espace monde
            lx, ly = px + nx * hw, py + ny * hw
            rx, ry = px - nx * hw, py - ny * hw

            u = lengths[i] / total_length
            alpha = (opacity_easing(t_life) if opacity_easing else 1.0) * opacity
        
            if self._textured:
                buf[vi * fpv + 0] = lx; buf[vi * fpv + 1] = ly
                buf[vi * fpv + 2] = u; buf[vi * fpv + 3] = 0.0
                buf[vi * fpv + 4] = alpha
                vi += 1
                buf[vi * fpv + 0] = rx; buf[vi * fpv + 1] = ry
                buf[vi * fpv + 2] = u; buf[vi * fpv + 3] = 1.0
                buf[vi * fpv + 4] = alpha
                vi += 1
            else:
                for vx, vy in ((lx, ly), (rx, ry)):
                    buf[vi * fpv + 0] = vx; buf[vi * fpv + 1] = vy
                    buf[vi * fpv + 2] = cr; buf[vi * fpv + 3] = cg
                    buf[vi * fpv + 4] = cb; buf[vi * fpv + 5] = alpha
                    vi += 1

        self._vertex_count = vi

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo[0])
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vi * fpv * 4, buf)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    # ======================================== DRAW ========================================
    def draw(self, pipeline: Pipeline, color: Color) -> None:
        """Envoie le mesh au GPU

        Args:
            pipeline: pipeline courant
            color: couleur RGBA *(tint en mode texturé)*
        """
        if not self._visible or self._vertex_count < 2:
            return

        mvp = pipeline.static_matrix @ pipeline.view_matrix

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glBindVertexArray(self._vao[0])

        if self._textured:
            prog = self._get_tex_program()
            prog.use()
            prog['u_mvp'] = mvp
            prog['u_tint'] = color.rgb
            prog['u_texture'] = 0
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture_id)
        else:
            prog = self._get_color_program()
            prog.use()
            prog['u_mvp'] = mvp

        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, self._vertex_count)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

    # ======================================== CLEANUP ========================================
    @property
    def visible(self) -> bool:
        """Visibilité"""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    @property
    def textured(self) -> bool:
        """Possède une texture"""
        return self._textured

    def delete(self) -> None:
        """Libère les ressources GPU"""
        gl.glDeleteVertexArrays(1, self._vao)
        gl.glDeleteBuffers(1, self._vbo)

# ======================================== HELPERS ========================================
def _catmull_rom(
    p0: tuple, p1: tuple, p2: tuple, p3: tuple, t: float,
) -> tuple[float, float, float, float, float]:
    """Évalue position + normale analytique sur une spline Catmull-Rom

    Returns:
        (x, y, age, nx, ny) avec (nx, ny) normale normalisée
    """
    t2 = t * t
    t3 = t2 * t

    x = 0.5 * (
        (2*p1[0]) +
        (-p0[0] + p2[0]) * t +
        (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
        (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        (2*p1[1]) +
        (-p0[1] + p2[1]) * t +
        (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
        (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
    )

    # Tangente analytique
    tx = 0.5 * (
        (-p0[0] + p2[0]) +
        2 * (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t +
        3 * (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t2
    )
    ty = 0.5 * (
        (-p0[1] + p2[1]) +
        2 * (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t +
        3 * (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t2
    )

    ln = math.sqrt(tx * tx + ty * ty)
    if ln > 1e-6:
        tx /= ln
        ty /= ln

    # Normale = perpendiculaire à la tangente
    nx, ny = -ty, tx

    age = p1[2] + (p2[2] - p1[2]) * t
    return x, y, age, nx, ny


def _perpendicular(ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """Vecteur perpendiculaire normalisé entre deux points"""
    dx, dy = bx - ax, by - ay
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return 0.0, 1.0
    return -dy / length, dx / length


def _normal_at(pt_list: list, i: int) -> tuple[float, float]:
    """Normale moyennée aux segments adjacents pour une polyline brute"""
    n = len(pt_list)
    if i == 0:
        return _perpendicular(
            pt_list[0][0], pt_list[0][1],
            pt_list[1][0], pt_list[1][1],
        )
    if i == n - 1:
        return _perpendicular(
            pt_list[-2][0], pt_list[-2][1],
            pt_list[-1][0], pt_list[-1][1],
        )
    nx1, ny1 = _perpendicular(
        pt_list[i-1][0], pt_list[i-1][1],
        pt_list[i][0],   pt_list[i][1],
    )
    nx2, ny2 = _perpendicular(
        pt_list[i][0],   pt_list[i][1],
        pt_list[i+1][0], pt_list[i+1][1],
    )
    nx, ny = (nx1 + nx2) * 0.5, (ny1 + ny2) * 0.5
    ln = math.sqrt(nx * nx + ny * ny)
    if ln > 1e-6:
        nx, ny = nx / ln, ny / ln
    return nx, ny

# ======================================== EXPORTS ========================================
__all__ = [
    "PygletTrailRenderer",
]