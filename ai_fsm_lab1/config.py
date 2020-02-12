""" Contains program configuration """

from nnet import TrainingData

WORLD_PATH = R"map\Map1.txt"
TRAIN_NET = True
NET_DATA = TrainingData(epochs=1000, set_size=20000, test_batch=100)
EVAL_MODE = True
EVAL_STEPS = 1000
FRAME_DELAY = 500
STEP_SIZE = 0.25

WINDOW_CAPTION = "Pathfinding Sandbox"
CELL_SIZE = 32
COL_DARK_CELL = (200, 200, 200)
COL_LIGHT_CELL = (255, 255, 255)
COL_WALL = (0, 0, 0)
COL_PLACE = (255, 200, 200)
