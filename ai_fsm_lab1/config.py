""" Contains program configuration """

from nnet import TrainingData

WORLD_PATH = R"map\Map2.txt"
PATH_MODE = 2
TRAIN_NET = False
NET_DATA = TrainingData(epochs=1000, set_size=2048, test_batch=100)
EVAL_MODE = False
EVAL_STEPS = 1000
FRAME_DELAY = 500
STEP_SIZE = 0.25

WINDOW_CAPTION = "Pathfinding Sandbox"
CELL_SIZE = 32
COL_DARK_CELL = (200, 200, 200)
COL_LIGHT_CELL = (255, 255, 255)
COL_WALL = (0, 0, 0)
COL_PLACE = (255, 200, 200)
