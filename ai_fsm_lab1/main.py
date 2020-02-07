"""Main file for demonstrang agent behaviour"""
from random import seed, randint
import pygame
import torch
from agent import Agent
from world import World
from nnet import CustomDataset, Net

if __name__ == "__main__":

    WORLD_PATH = R"map\Map1.txt"
    TRAIN_NET = True
    TRAIN_ITERATIONS = 10

    seed(WORLD_PATH)

    WORLD = World.from_map(WORLD_PATH)
    WORLD.place_random("ltu", "travven", "dallas", "ica", "coop", "brännarvägen", "morö backe", "frögatan 154", "frögatan 181", "staregatan")

    if TRAIN_NET:
        train = CustomDataset(WORLD, TRAIN_ITERATIONS)
        test = CustomDataset(WORLD, TRAIN_ITERATIONS)
        net = Net(WORLD.width, WORLD.height)
        net.train(train, test)


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

    pygame.init()

    # INIT PYGAME
    CELL_SIZE = 32
    SCREEN = pygame.display.set_mode((CELL_SIZE * WORLD.width, CELL_SIZE * WORLD.height))
    pygame.display.set_caption("Pathfinding Sandbox")

    COL_DARK_CELL = pygame.color.Color(200, 200, 200)
    COL_LIGHT_CELL = pygame.color.Color(255, 255, 255)
    COL_WALL = pygame.color.Color(0, 0, 0)
    COL_PLACE = pygame.color.Color(255, 200, 200)

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break

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
                path = agent.state.route
                for p in range(len(path) - 1):
                    p1 = (int((path[p][0] + 0.5) * CELL_SIZE), int((path[p][1] + 0.5) * CELL_SIZE))
                    p2 = (int((path[p + 1][0] + 0.5) * CELL_SIZE), int((path[p + 1][1] + 0.5) * CELL_SIZE))
                    pygame.draw.line(SCREEN, agent.color, p1, p2)


        pygame.display.flip()
        WORLD.step_forward(0.25)
        pygame.time.delay(500)
