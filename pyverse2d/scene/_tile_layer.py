# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from .._flag import CameraMode
from .._rendering._pipeline import Pipeline
from ..abc import Layer
from ..tile._tile_map import TileMap

import pyglet
import pyglet.image
from pyglet.graphics import Batch, Group

from numbers import Real

# ======================================== LAYER ========================================
class TileLayer(Layer):
    """
    Layer affichant un TileMap

    Args:
        tile_map(TileMap): couche de tuiles à afficher
        parallax(tuple[float, float], optional): facteur de parallax (x, y) ; (1, 1) = suit la caméra normalement
    """
    def __init__(
        self,
        tile_map: TileMap,
        parallax: tuple[Real, Real] = (1.0, 1.0),
        camera_mode: CameraMode = CameraMode.WORLD,
    ):
        super().__init__(camera_mode)
        self._tile_map: TileMap = expect(tile_map, TileMap)
        self._parallax: tuple[float, float] = (
            float(positive(expect(parallax[0], Real))),
            float(positive(expect(parallax[1], Real))),
        )

        # Cache : image source + régions par tile_id + sprites par (col, row)
        self._image: pyglet.image.AbstractImage | None = None
        self._regions: dict[int, pyglet.image.TextureRegion] = {}
        self._sprites: dict[tuple[int, int], pyglet.sprite.Sprite] = {}
        self._batch: Batch = Batch()
        self._group: Group = Group(order=0)

    # ======================================== GETTERS ========================================
    @property
    def tile_map(self) -> TileMap:
        """Renvoie le TileMap assigné"""
        return self._tile_map

    @property
    def parallax(self) -> tuple[float, float]:
        """Renvoie le facteur de parallax"""
        return self._parallax

    # ======================================== SETTERS ========================================
    @tile_map.setter
    def tile_map(self, value: TileMap) -> None:
        """Fixe le TileMap assigné — réinitialise le cache"""
        self._tile_map = expect(value, TileMap)
        self._invalidate_cache()

    @parallax.setter
    def parallax(self, value: tuple[Real, Real]) -> None:
        """Fixe le facteur de parallax"""
        self._parallax = (
            float(positive(expect(value[0], Real))),
            float(positive(expect(value[1], Real))),
        )

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self):
        """Activation du layer"""
        ...

    def on_stop(self):
        """Désactivation du layer"""
        self._invalidate_cache()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """Actualisation du layer"""
        ...

    def draw(self, pipeline: Pipeline):
        """
        Affichage du layer
        Args:
            pipeline(Pipeline): pipeline active
        """
        self._ensure_image()
        if self._image is None:
            return

        cam = pipeline.camera
        screen = pipeline.screen

        # Position caméra avec parallax appliqué
        px = cam.final_x * self._parallax[0]
        py = cam.final_y * self._parallax[1]

        # Région visible en coordonnées monde
        col_min, row_min, col_max, row_max = self._tile_map.tiles_in_region(
            px - screen.half_width,
            py - screen.half_height,
            screen.width,
            screen.height,
        )

        tm = self._tile_map

        visible = set()
        for row in range(row_min, row_max):
            for col in range(col_min, col_max):
                tile_id = tm.tile_at(col, row)
                if tile_id == 0:
                    continue

                key = (col, row)
                visible.add(key)

                if key not in self._sprites:
                    region = self._get_region(tile_id)
                    if region is None:
                        continue

                    wx, wy = tm.tile_to_world(col, row)
                    sprite = pyglet.sprite.Sprite(
                        region,
                        x=wx, y=wy,
                        batch=self._batch,
                        group=self._group,
                    )
                    sprite.scale_x = tm.tile_width  / region.width
                    sprite.scale_y = tm.tile_height / region.height
                    self._sprites[key] = sprite

        # Nettoyage des sprites hors champ
        for key in list(self._sprites):
            if key not in visible:
                self._sprites.pop(key).delete()

        self._batch.draw()

    # ======================================== INTERNALS ========================================
    def _ensure_image(self) -> None:
        """Charge l'image source si elle n'est pas encore en cache"""
        if self._image is not None:
            return
        try:
            self._image = pyglet.image.load(self._tile_map.tile.image_path)
        except FileNotFoundError:
            print(f"[TileLayer] Image introuvable : {self._tile_map.tile.image_path}")
            self._image = None

    def _get_region(self, tile_id: int) -> pyglet.image.TextureRegion | None:
        """Renvoie la région de texture pour un tile_id, avec mise en cache"""
        if tile_id in self._regions:
            return self._regions[tile_id]

        tile = self._tile_map.tile
        tw = int(tile.tile_width)
        th = int(tile.tile_height)
        margin = int(tile.margin)
        spacing = int(tile.spacing)
        stride = tw + spacing
        cols = (self._image.width - margin) // stride

        if cols <= 0:
            return None

        col = tile_id % cols
        row = tile_id // cols
        x = margin + col * stride

        y_tiled = margin + row * (th + spacing)
        y_pyglet = self._image.height - y_tiled - th

        region = self._image.get_region(x, y_pyglet, tw, th).get_texture()
        self._regions[tile_id] = region
        return region

    def _invalidate_cache(self) -> None:
        """Libère tous les sprites et régions en cache"""
        for sprite in self._sprites.values():
            sprite.delete()
        self._sprites.clear()
        self._regions.clear()
        self._image = None