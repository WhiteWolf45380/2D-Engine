# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline

import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.graphics import Group
from pyglet.graphics.vertexdomain import VertexList

# ======================================== SHADERS ========================================
_VERT = """
#version 330 core
in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

_FRAG = """
#version 330 core
uniform vec4 color;
out vec4 out_color;
void main() {
    out_color = color;
}
"""

# ======================================== GROUP ========================================
class _AmbientGroup(Group):
    """Group appliquant le shader d'ambiance"""

    def __init__(self, program: ShaderProgram, order: int = 0, parent: Group = None):
        super().__init__(order=order, parent=parent)
        self.program = program

    def set_state(self):
        self.program.use()
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        self.program.stop()
        gl.glDisable(gl.GL_BLEND)

# ======================================== RENDERER ========================================
class LightRenderer:
    """Renderer de lumière"""
    __slots__ = ("_vlist", "_group")

    _program: ShaderProgram = None

    def __init__(self):
        self._vlist: VertexList = None
        self._group: _AmbientGroup = None

    @classmethod
    def _get_program(cls) -> ShaderProgram:
        if cls._program is None:
            cls._program = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_FRAG, 'fragment'),
            )
        return cls._program

    def render_ambient(self, pipeline: Pipeline, tint: tuple[int, int, int], ambient: float, z: int = 0) -> None:
        """Applique l'ambiance lumineuse

        Args:
            pipeline: pipeline de rendu
            tint: couleur de teinte (r, g, b) normalisée [0, 1]
            ambient: luminosité ambiante [0, 1]
            z: z-order dans le batch
        """
        # Couleur
        r, g, b = tint
        a = 1.0 - ambient

        # Vertices
        wx, wy, ww, wh = pipeline.gl_viewport

        x0, y0 = wx, wy
        x1, y1 = wx + ww, wy
        x2, y2 = wx + ww, wy + wh
        x3, y3 = wx, wy + wh

        # Passage en NDC
        fw, fh = pipeline.window.size
        def to_ndc(x: float, y: float) -> tuple[float, float]:
            return (x / fw) * 2 - 1, (y / fh) * 2 - 1
        
        nx0, ny0 = to_ndc(x0, y0)
        nx1, ny1 = to_ndc(x1, y1)
        nx2, ny2 = to_ndc(x2, y2)
        nx3, ny3 = to_ndc(x3, y3)

        # Calcul du quad
        mesh = [
            nx0, ny0, nx1, ny1, nx2, ny2,
            nx0, ny0, nx2, ny2, nx3, ny3,
        ]

        # Program & uniforms
        program = self._get_program()
        program['color'] = (r, g, b, a)

        # Group (lazy, parent = z-group du layer)
        if self._group is None:
            self._group = _AmbientGroup(
                program,
                order=0,
                parent=pipeline.get_group(z=z)
            )

        # VertexList dans le batch de la scène
        if self._vlist is None:
            self._vlist = program.vertex_list(6, gl.GL_TRIANGLES,
                batch=pipeline.batch,
                group=self._group,
                position=('f', mesh),
            )
        else:
            self._vlist.position[:] = mesh