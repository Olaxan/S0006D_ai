"""Main file for demonstating agent behaviour"""

from random import seed

from world import World
from config import WORLD_PATH, STEP_SIZE
from unitplanner import UnitPlanner

if __name__ == "__main__":

    seed(WORLD_PATH)

    WORLD = World.from_map(WORLD_PATH)
    MANAGERS = [
        UnitPlanner(WORLD)
    ]

    for mgr in MANAGERS:
        mgr.start()

    while True:
        WORLD.step_forward(STEP_SIZE)