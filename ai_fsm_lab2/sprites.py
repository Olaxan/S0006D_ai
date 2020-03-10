from random import randint, random

import pygame as pg

from config import *
from world import TerrainTypes

def variant(col, low, high):
    r, g, b = col
    rand = randint(low, high)
    return (r + rand, g + rand, b + rand)

class Tile(pg.sprite.Sprite):
    def __init__(self, game, x, y, expand=0):
        self.groups = game.all_sprites, game.fog
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILE_SIZE + expand * 2, TILE_SIZE + expand * 2))
        self.image.fill(COL_BG)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILE_SIZE - expand
        self.rect.y = y * TILE_SIZE - expand

class Ground(Tile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.image.fill(variant(COL_GROUND, -10, 10))

class Rock(Tile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.image.fill(variant(COL_ROCK, -20, 20))

class Water(Tile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.image.fill(COL_WATER)

    def update(self):
        self.image.fill(variant(COL_WATER, -5, 5))

class Swamp(Tile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.image.fill(COL_SWAMP)

    def update(self):
        self.image.fill(variant(COL_SWAMP, -10, 10))

class Tree(Tile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.image.fill(COL_GROUND)
        self.game.world.graph.on_terrain_changed.append(self.on_changed)
        pg.draw.circle(self.image, COL_TREE, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)

    def on_changed(self, cell, terrain):
        if (self.x, self.y) == cell and terrain == TerrainTypes.Stump:
            Ground(self.game, self.x, self.y)
            del self

class UnitSprite(pg.sprite.Sprite):

    unit_colors = {

    }

    def __init__(self, game, agent):
        self.groups = game.all_sprites, game.non_fog
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILE_SIZE - 8, TILE_SIZE - 8))
        self.image.fill(COL_UNIT)
        self.rect = self.image.get_rect()
        self.agent = agent

    def update(self):
        self.rect.x = self.agent.x * TILE_SIZE + 4
        self.rect.y = self.agent.y * TILE_SIZE + 4
        self.image.fill(self.agent.color)
