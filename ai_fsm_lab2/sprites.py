from random import randint
import pygame as pg
from config import *

def variant(col, low, high):
    r, g, b = col
    rand = randint(low, high)
    return (r + rand, g + rand, b + rand)

class Tile(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(COL_BG)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

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
        self.image.fill(variant(COL_TREE, -20, 20))
