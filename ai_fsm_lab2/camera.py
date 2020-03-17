import pygame as pg
from config import CAMERA_SPEED, CAMERA_SHIFT

class Camera:
    def __init__(self, x, y, width, height):
        self.camera = pg.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, dt):
        keys = pg.key.get_pressed()
        mult = CAMERA_SHIFT if keys[pg.K_LSHIFT] else 1
        x = ((keys[pg.K_RIGHT] or keys[pg.K_d]) - (keys[pg.K_LEFT] or keys[pg.K_a])) * CAMERA_SPEED * mult * dt
        y = ((keys[pg.K_DOWN] or keys[pg.K_s]) - (keys[pg.K_UP] or keys[pg.K_w])) * CAMERA_SPEED * mult * dt
        self.move(x, y)

    def move(self, x, y):
        self.x -= x
        self.y -= y
        self.camera = pg.Rect(self.x, self.y, self.width, self.height)
