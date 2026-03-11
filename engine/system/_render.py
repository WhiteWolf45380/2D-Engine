# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet
import pyglet.shapes
import pyglet.sprite
import pyglet.text
import pyglet.image

from ..ecs import System, World
from ..component import Transform, SpriteRenderer, ShapeRenderer, TextRenderer
from ..shape import Capsule, Circle, Rect, Ellipse, Segment, Polygon

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .._rendering import Renderer

# ======================================== INTERNAL SHAPES ========================================
class _CapsuleShape:
    def __init__(self, x, y, radius, spine, batch=None, group=None):
        self._rect = pyglet.shapes.Rectangle(x - radius, y, radius * 2, spine, batch=batch, group=group)
        self._top = pyglet.shapes.Circle(x, y + spine, radius, batch=batch, group=group)
        self._bottom = pyglet.shapes.Circle(x, y, radius, batch=batch, group=group)

    @property
    def visible(self): 
        return self._rect.visible

    @visible.setter
    def visible(self, v): 
        self._rect.visible = self._top.visible = self._bottom.visible = v

    @property
    def x(self): 
        return self._bottom.x

    @x.setter
    def x(self, v):
        self._bottom.x = v
        self._top.x = v
        self._rect.x = v - self._bottom.radius

    @property
    def y(self):
        return self._bottom.y

    @y.setter
    def y(self, v):
        self._bottom.y = v
        self._top.y = v + self._rect.height
        self._rect.y = v

    @property
    def opacity(self):
        return self._rect.opacity

    @opacity.setter
    def opacity(self, v):
        self._rect.opacity = self._top.opacity = self._bottom.opacity = v

    def delete(self):
        self._rect.delete()
        self._top.delete()
        self._bottom.delete()

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu des renderers avec cache"""
    def __init__(self):
        self._sprites: dict[str, pyglet.sprite.Sprite] = {}
        self._shapes: dict[str, object] = {}
        self._labels: dict[str, pyglet.text.Label] = {}
        self._image_cache: dict[str, pyglet.image.AbstractImage] = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """Actualisation"""
        ...

    # ======================================== DRAW ========================================
    def draw(self, world: World, renderer: Renderer):
        """
        Synchronise les entités avec les objets pyglet du Batch

        Args:
            world(World): monde à rendre
            renderer(Renderer): renderer actif
        """
        self._draw_sprites(world, renderer)
        self._draw_shapes(world, renderer)
        self._draw_texts(world, renderer)

        # Nettoyage des entités supprimées
        active_ids = {e.id for e in world.query(SpriteRenderer)}
        for eid in list(self._sprites):
            if eid not in active_ids:
                self._sprites.pop(eid).delete()

        active_ids = {e.id for e in world.query(ShapeRenderer)}
        for eid in list(self._shapes):
            if eid not in active_ids:
                self._shapes.pop(eid).delete()

        active_ids = {e.id for e in world.query(TextRenderer)}
        for eid in list(self._labels):
            if eid not in active_ids:
                self._labels.pop(eid).delete()

    # ======================================== SPRITES ========================================
    def _draw_sprites(self, world: World, renderer: Renderer):
        """Synchronise les entités SpriteRenderer"""
        for entity in world.query(SpriteRenderer, Transform):
            sr: SpriteRenderer = entity.get(SpriteRenderer)
            tr: Transform = entity.get(Transform)

            if not sr.is_visible():
                if entity.id in self._sprites:
                    self._sprites[entity.id].visible = False
                continue

            raw = self._load_image(sr.image.path)
            if raw is None:
                continue

            if entity.id not in self._sprites:
                group = renderer.get_group(sr.z)
                self._sprites[entity.id] = pyglet.sprite.Sprite(
                    raw,
                    batch=renderer.batch,
                    group=group,
                )

            sprite = self._sprites[entity.id]
            sprite.visible = True
            sprite.x = tr.x + sr.offset[0]
            sprite.y = tr.y + sr.offset[1]
            sprite.rotation = tr.rotation
            sprite.scale = tr.scale * sr.image.scale
            sprite.opacity = int(sr.get_alpha() * 255)

            if sr.image.flip_x or sr.image.flip_y:
                sprite.scale_x = -sprite.scale_x if sr.image.flip_x else sprite.scale_x
                sprite.scale_y = -sprite.scale_y if sr.image.flip_y else sprite.scale_y

    # ======================================== SHAPES ========================================
    def _draw_shapes(self, world: World, renderer: Renderer):
        """Synchronise les entités ShapeRenderer"""
        for entity in world.query(ShapeRenderer, Transform):
            sr: ShapeRenderer = entity.get(ShapeRenderer)
            tr: Transform = entity.get(Transform)

            if not sr.is_visible():
                if entity.id in self._shapes:
                    self._shapes[entity.id].visible = False
                continue

            x = tr.x + sr.offset[0]
            y = tr.y + sr.offset[1]

            if entity.id not in self._shapes:
                group = renderer.get_group(sr.z)
                shape = sr.shape
                obj = self._create_shape(shape, x, y, renderer.batch, group)
                if obj is None:
                    continue
                self._shapes[entity.id] = obj

            obj = self._shapes[entity.id]
            obj.visible = True
            obj.x = x
            obj.y = y
            obj.opacity = int(sr.get_alpha() * 255)

    def _create_shape(self, shape, x, y, batch, group):
        """Crée l'objet pyglet.shapes correspondant"""
        if isinstance(shape, Capsule):
            return _CapsuleShape(x, y, shape.radius, shape.spine, batch=batch, group=group)
        if isinstance(shape, Circle):
            return pyglet.shapes.Circle(x, y, shape.radius, batch=batch, group=group)
        if isinstance(shape, Rect):
            return pyglet.shapes.Rectangle(x, y, shape.width, shape.height, batch=batch, group=group)
        if isinstance(shape, Ellipse):
            return pyglet.shapes.Ellipse(x, y, shape.rx, shape.ry, batch=batch, group=group)
        if isinstance(shape, Segment):
            ax, ay = shape.A
            bx, by = shape.B
            return pyglet.shapes.Line(ax, ay, bx, by, width=shape.width, batch=batch, group=group)
        if isinstance(shape, Polygon):
            pts = [(p.x, p.y) for p in shape.points]
            return pyglet.shapes.Polygon(*pts, batch=batch, group=group)

    # ======================================== TEXTES ========================================
    def _draw_texts(self, world: World, renderer: Renderer):
        """Synchronise les entités TextRenderer"""
        for entity in world.query(TextRenderer, Transform):
            tr_c: TextRenderer = entity.get(TextRenderer)
            tr: Transform = entity.get(Transform)

            if not tr_c.is_visible():
                if entity.id in self._labels:
                    self._labels[entity.id].visible = False
                continue

            if entity.id not in self._labels:
                group = renderer.get_group(tr_c.z)
                t = tr_c.text
                self._labels[entity.id] = pyglet.text.Label(
                    t.text,
                    font_name=t.font,
                    font_size=t.fontsize,
                    color=t.color,
                    batch=renderer.batch,
                    group=group,
                )

            label = self._labels[entity.id]
            label.visible = True
            label.x = tr.x + tr_c.offset[0]
            label.y = tr.y + tr_c.offset[1]
            label.opacity = int(tr_c.get_alpha() * 255)

    # ======================================== IMAGE CACHE ========================================
    def _load_image(self, path: str) -> pyglet.image.AbstractImage | None:
        """Charge et cache une image depuis son chemin"""
        if path in self._image_cache:
            return self._image_cache[path]
        try:
            img = pyglet.image.load(path)
            self._image_cache[path] = img
            return img
        except FileNotFoundError:
            print(f"[RenderSystem] Cannot load image: {path}")
            return None