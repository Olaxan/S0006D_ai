"""Main file for demonstating agent behaviour"""
from __future__ import annotations

import os.path as io
from random import randint, seed

import pygame
from tqdm import tqdm

from agent import Agent
from config import *
from nnet import NeuralHeuristic
from world import World


def draw_world():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            cell = (pos[0] // CELL_SIZE, pos[1] // CELL_SIZE)
            if WORLD.graph.is_free(cell):
                WORLD.graph.walls.append(cell)
            else:
                WORLD.graph.walls.remove(cell)


    for y in range(WORLD.height):
        for x in range(WORLD.width):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = COL_LIGHT_CELL if (x + y) % 2 == 0 else COL_DARK_CELL
            pygame.draw.rect(SCREEN, color, rect)

    for wall in WORLD.graph.walls:
        rect = pygame.Rect(wall[0] * CELL_SIZE, wall[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(SCREEN, COL_WALL, rect)

    for place in WORLD.locations.values():
        rect = pygame.Rect(place[0] * CELL_SIZE + 3, place[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
        pygame.draw.rect(SCREEN, COL_PLACE, rect)

    for agent in AGENTS:
        rect = pygame.Rect(agent.x * CELL_SIZE + 10, agent.y * CELL_SIZE + 10, CELL_SIZE - 20, CELL_SIZE - 20)
        pygame.draw.rect(SCREEN, agent.color, rect)

        if agent.is_walking:
            path = agent.state.path
            for p in range(len(path) - 1):
                p1 = (int((path[p][0] + 0.5) * CELL_SIZE), int((path[p][1] + 0.5) * CELL_SIZE))
                p2 = (int((path[p + 1][0] + 0.5) * CELL_SIZE), int((path[p + 1][1] + 0.5) * CELL_SIZE))
                pygame.draw.line(SCREEN, agent.color, p1, p2)

    pygame.display.flip()

if __name__ == "__main__":

    seed(WORLD_PATH)

    WORLD = World.from_map(WORLD_PATH)
    WORLD.place_random("ltu", "travven", "dallas", "ica", "coop", "brännarvägen", "morö backe", "frögatan 154", "frögatan 181", "staregatan")

    if TRAIN_NET:   # Init neural pathing if desired
        NET_PATH = "{}_{}-{}.pth".format(io.splitext(WORLD_PATH)[0], NET_DATA.epochs, NET_DATA.set_size)
        NET_MODEL = NeuralHeuristic(WORLD, NET_PATH, NET_DATA)
        WORLD.heuristic = NET_MODEL
        NET_MODEL.save(NET_PATH)

    AGENTS = [
        Agent(WORLD, "Semlo", "frögatan 154", "coop"),
        Agent(WORLD, "Lukas", "morö backe", "dallas"),
        Agent(WORLD, "Sahmon", "frögatan 181", "ltu"),
        #Agent(WORLD, "Spenus", "staregatan", "ltu"),
        #Agent(WORLD, "Gurke", "brännarvägen", "ica")
    ]

    for agent in AGENTS:
        agent.start()
        agent.color = pygame.color.Color(randint(0, 200), randint(0, 200), randint(0, 200))

    if not EVAL_MODE: # INIT PYGAME
        pygame.init()
        SCREEN = pygame.display.set_mode((CELL_SIZE * WORLD.width, CELL_SIZE * WORLD.height))
        pygame.display.set_caption(WINDOW_CAPTION)

        while True:
            WORLD.step_forward(STEP_SIZE)
            draw_world()
            pygame.time.delay(FRAME_DELAY)
    else:
        print("Evaluating performance...")
        for frame in tqdm(range(EVAL_STEPS)):
            WORLD.step_forward(STEP_SIZE)

        per_query = WORLD.path_time / WORLD.path_queries
        print("Pathfinding took {:.4} seconds over {} queries (~{:.4} s/q)".format(WORLD.path_time, WORLD.path_queries, per_query))

# ============== FUNCTIONS ================
