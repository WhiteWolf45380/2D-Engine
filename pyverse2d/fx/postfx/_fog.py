# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import over, clamped, positive
from ..._rendering import Pipeline
from ...abc import PostFxEffect
from ...asset import Color

from ._specialized_renderer import SpecializedPostFxRenderer
from ._mask import MaskData, GLSL_MASK

from pyglet.graphics.shader import Shader, ShaderProgram

from dataclasses import dataclass
from numbers import Real, Integral
from typing import ClassVar
import math

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

_FRAG = f"""
#version 330 core
uniform sampler2D u_texture;
uniform vec2  u_wind;        // direction + vitesse en UV/s
uniform float u_time;
uniform float u_density;     // seuil de densité [0, 1]
uniform float u_softness;    // largeur du fondu (> 0)
uniform float u_scale;       // zoom du bruit (> 0)
uniform int   u_octaves;     // octaves fBm [1, 8]
uniform float u_lacunarity;  // fréquence entre octaves
uniform float u_gain;        // atténuation entre octaves
uniform vec3  u_color;       // couleur du brouillard
in vec2 v_uv;
out vec4 out_color;

{GLSL_MASK}

// ---- Hash sans texture ----
float hash(vec2 p) {{
    p = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y);
}}

// ---- Bruit bilinéaire ----
float noise(vec2 p) {{
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);   // smoothstep

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}}

// ---- Fractal Brownian Motion ----
float fbm(vec2 p) {{
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    for (int i = 0; i < u_octaves; i++) {{
        value     += amplitude * noise(p * frequency);
        frequency *= u_lacunarity;
        amplitude *= u_gain;
    }}
    return value;
}}

void main() {{
    vec4  orig = texture(u_texture, v_uv);
    float mask = compute_mask();

    // UV animés par le vent
    vec2 uv = v_uv * u_scale + u_wind * u_time;

    // fBm en deux couches décalées pour plus d'organicité
    float n  = fbm(uv);
    float n2 = fbm(uv + vec2(3.7, 1.4));  // décalage de domaine
    float fog = fbm(uv + vec2(n, n2));

    // Seuil soft
    float alpha = smoothstep(u_density, u_density + max(u_softness, 0.001), fog);

    vec3 fogged = mix(orig.rgb, u_color, alpha);
    out_color   = vec4(mix(orig.rgb, fogged, mask), orig.a);
}}
"""

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Fog(PostFxEffect):
    """Effet post-processing: brouillard procédural animé

    Génère un brouillard volumétrique 2D via fractal Brownian motion (fBm).
    Le vent anime le déplacement du bruit frame par frame via l'horloge interne.

    Args:
        angle: angle du vent en degrés *(0 = droite)*
        velocity: vitesse du vent en unités monde par second *(> 0)*
        density: seuil d'apparition du brouillard *[0, 1]* — plus bas = plus dense
        softness: largeur du fondu entre brouillard et scène *(>= 0)*
        scale: zoom du bruit procédural *(> 0)* - plus bas = nuages plus grands
        octaves: nombre d'octaves fBm *[1, 8]* - plus élevé = plus de détail
        lacunarity: facteur de fréquence entre octaves *(> 1)*
        gain: facteur d'amplitude entre octaves *]0, 1[*
        color: couleur RGB du brouillard
    """
    angle: Real = 0.0
    velocity: Real = 0.05
    density: Real = 0.4
    softness: Real = 0.3
    scale: Real = 3.0
    octaves: Integral = 5
    lacunarity: Real = 2.0
    gain: Real = 0.5
    color: tuple = (1.0, 1.0, 1.0)

    _ID: ClassVar[str] = "fog"

    def __post_init__(self) -> None:
        object.__setattr__(self, "angle", float(self.angle))
        object.__setattr__(self, "velocity", float(self.velocity))
        object.__setattr__(self, "density", float(self.density))
        object.__setattr__(self, "softness", float(self.softness))
        object.__setattr__(self, "scale", float(self.scale))
        object.__setattr__(self, "octaves", int(self.octaves))
        object.__setattr__(self, "lacunarity", float(self.lacunarity))
        object.__setattr__(self, "gain", float(self.gain))
        object.__setattr__(self, "color", tuple(float(c) for c in self.color))

        if __debug__:
            clamped(self.density)
            positive(self.softness)
            over(self.scale, 0, include=False)
            over(self.octaves, 1, include=True)
            over(self.lacunarity, 1.0, include=False)
            clamped(self.gain, include_min=False, include_max=False)
            over(self.velocity, 0, include=False)

# ======================================== RENDERER ========================================
class FogPostFxRenderer(SpecializedPostFxRenderer):
    """Renderer spécialisé pour l'effet ``Fog``"""
    __slots__ = tuple()

    _HANDLES: ClassVar[frozenset[type[PostFxEffect]]] = frozenset({Fog})
    _REQUIRES_TIME: ClassVar[bool] = True
    _program: ClassVar[ShaderProgram | None] = None
    _time: ClassVar[float] = 0.0

    @classmethod
    def _get_program(cls) -> ShaderProgram:
        if cls._program is None:
            cls._program = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_FRAG, 'fragment'))
        return cls._program

    @classmethod
    def clear_shader_cache(cls) -> None:
        cls._program = None

    def apply(self, pipeline: Pipeline, effect: Fog, mask: MaskData) -> None:
        """Applique le brouillard procédural

        Args:
            pipeline: ``Pipeline`` de rendu courant
            effect: paramètres du brouillard
            mask: données de masque spatial
        """
        theta = math.radians(effect.angle)
        vx, vy = pipeline.scale_to_framebuffer(effect.velocity, effect.velocity)
        wind = (
            math.cos(theta) * vx,
            math.sin(theta) * vy,
        )

        pipeline.apply_shader(
            self._get_program(),
            u_wind=wind,
            u_time=self._time,
            u_density=effect.density,
            u_softness=effect.softness,
            u_scale=effect.scale,
            u_octaves=effect.octaves,
            u_lacunarity=effect.lacunarity,
            u_gain=effect.gain,
            u_color=effect.color,
            **mask.as_uniforms(),
        )

# ======================================== EXPORTS ========================================
__all__ = [
    "Fog",
    "FogPostFxRenderer",
]