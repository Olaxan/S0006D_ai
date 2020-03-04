"""Main file for agent behaviour"""

from __future__ import annotations

from random import seed, randint

import pygame

from config import *
from resmgr import ResourceManager
from unitmgr import UnitManager
from world import World, TerrainTypes
from utils import Clamped

def in_view(cell, view, zoom):
    return cell[0] > view[0] and cell[0] < view[0] + zoom and cell[1] > view[1] and cell[1] < view[1] + zoom

def variant(col, lo=-20, hi=20):
    r, g, b = col
    k = randint(lo, hi)
    return (r + k, g + k, b + k)

if __name__ == "__main__":

    seed(WORLD_PATH)

    WORLD = World.from_map(WORLD_PATH)
    MANAGERS = [
        UnitManager(WORLD),
        ResourceManager(WORLD)
    ]

    for mgr in MANAGERS:
        mgr.start()

    pygame.init()
    SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_CAPTION)

    ZOOM = Clamped(1, 1, 10)

    VIEW_X = 0
    VIEW_Y = 0
    VIEW_ZOOM = 100

    while True:

        ZOOM_SIZE = max(WINDOW_WIDTH, WINDOW_HEIGHT) / VIEW_ZOOM

        WORLD.step_forward(STEP_SIZE)

        SCREEN.fill(COL_DARK_CELL)

        KEYS = pygame.key.get_pressed()  #checking pressed keys
        MULT = 1 if KEYS[pygame.K_LSHIFT] else PAN_SHIFT_MULT
        VIEW_X += ((KEYS[pygame.K_d]) - (KEYS[pygame.K_a])) * PAN_SIZE * MULT
        VIEW_Y += ((KEYS[pygame.K_s]) - (KEYS[pygame.K_w])) * PAN_SIZE * MULT

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                VIEW_ZOOM += ((event.button == 5) - (event.button == 4)) * ZOOM_STEP

        for i in range(VIEW_ZOOM ** 2):
            local_x = i % VIEW_ZOOM
            local_y = i // VIEW_ZOOM
            x = VIEW_X + local_x
            y = VIEW_Y + local_y
            rect = pygame.Rect(local_x * ZOOM_SIZE - 1, local_y * ZOOM_SIZE - 1, ZOOM_SIZE + 2, ZOOM_SIZE + 2)
            if WORLD.graph.is_in_bounds((x, y)):
                terrain = WORLD.graph.get_terrain(x, y)[0].value
                if terrain is not TerrainTypes.Ground:
                    pygame.draw.rect(SCREEN, terrain, rect)
            else:
                pygame.draw.rect(SCREEN, 0, rect)


        pygame.display.flip()

# ============== FUNCTIONS ==============