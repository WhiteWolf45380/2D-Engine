# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline

from pyglet.graphics.shader import Shader, ShaderProgram

# ======================================== SHADERS ========================================
_VERT = """
#version 330 core
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

_FRAG_AMBIENT = """
#version 330 core
uniform sampler2D u_texture;
uniform float u_ambient;
in vec2 v_uv;
out vec4 out_color;
void main() {
    vec4 pixel = texture(u_texture, v_uv);
    out_color = vec4(pixel.rgb * u_ambient, pixel.a);
}
"""

_FRAG_TINT = """
#version 330 core
uniform sampler2D u_texture;
uniform vec3 u_tint;
uniform float u_strength;
in vec2 v_uv;
out vec4 out_color;
void main() {
    vec4 pixel = texture(u_texture, v_uv);
    out_color = vec4(mix(pixel.rgb, pixel.rgb * u_tint, u_strength), pixel.a);
}
"""

# ======================================== RENDERER ========================================
class LightRenderer:
    """Renderer de lumière"""
    __slots__ = ()

    _ambient_program: ShaderProgram = None
    _tint_program: ShaderProgram = None

    # ======================================== PROGRAMS ========================================
    @classmethod
    def _get_ambient_program(cls) -> ShaderProgram:
        if cls._ambient_program is None:
            cls._ambient_program = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_FRAG_AMBIENT, 'fragment'),
            )
        return cls._ambient_program

    @classmethod
    def _get_tint_program(cls) -> ShaderProgram:
        if cls._tint_program is None:
            cls._tint_program = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_FRAG_TINT, 'fragment'),
            )
        return cls._tint_program

    # ======================================== AMBIENT ========================================
    def render_ambient(self, pipeline: Pipeline, ambient: float) -> None:
        """Applique la luminosité ambiante

        Args:
            pipeline: pipeline de rendu
            ambient: luminosité [0, 1] — 0 = noir total, 1 = pleine luminosité
        """
        pipeline.apply_shader(self._get_ambient_program(), u_ambient=ambient)

    # ======================================== TINT ========================================
    def render_tint(self, pipeline: Pipeline, tint: tuple[float, float, float], strength: float) -> None:
        """Applique une teinte colorée

        Args:
            pipeline: pipeline de rendu
            tint: couleur RGB normalisée [0.0, 1.0]
            strength: force de la teinte [0, 1]
        """
        pipeline.apply_shader(self._get_tint_program(), u_tint=tint, u_strength=strength)