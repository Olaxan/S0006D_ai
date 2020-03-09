""" Contains program configuration """

from os import path

GAME_PATH = path.dirname(__file__)
WORLD_PATH = path.join(GAME_PATH, 'map/Map1.txt')
WORLD_BG_PATH = path.join(GAME_PATH, 'map/Map1.bmp')
BACKGROUND_PATH = path.join(GAME_PATH, 'res/bg.jpg')

TIME_SCALE = 5
WORLD_SCALE = 1 # meters per cell
WORLD_TREES_PER_CELL = 5
WORLD_ORE_COUNT = 50
HAS_FOG = True

TILE_SIZE = 16

FPS = 60
WINDOW_CAPTION = "Blorf 3.0"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
CAMERA_SPEED = 10 * TILE_SIZE
CAMERA_SHIFT = 5

COL_BG = (0, 0, 0)
COL_GROUND = (76, 108, 36)
COL_ROCK = (90, 77, 65)
COL_WATER = (156, 211, 219)
COL_SWAMP = (80, 102, 53)
COL_TREE = (200, 180, 50)
COL_ORE = (70, 50, 50)
COL_UNIT = (255, 255, 0)
COL_WORKER = (255, 125, 0)
COL_SCOUT = (255, 0, 255)

INIT_UNITS = 10
INIT_SCOUT = 5
INIT_WORKER_COAL = 1
INIT_WORKER_BUILDER = 1
INIT_WORKER_SMELTERY = 1

UNIT_SPEED = 1
UNIT_SPEED_SCOUT = 2
UNIT_SCOUT_RANGE = 20

TIME_TRAIN_SCOUT = 5
TIME_TRAIN_BUILDER = 5
TIME_CHOP_TREE = 10
