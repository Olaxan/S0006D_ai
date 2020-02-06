import sys, time, pygame
from agent import Agent
from world import World
from path import WeightedGrid

if __name__ == "__main__":

    world = World.from_map(R"map\Map1.txt")
    world.place_random("ltu", "travven", "dallas", "ica", "coop", "brännarvägen", "morö backe", "frögatan 154", "frögatan 181", "staregatan")

    agents = [
        Agent(world, "Semlo", "frögatan 154", "coop"),
        Agent(world, "Lukas", "morö backe", "dallas"),
        Agent(world, "Sahmon", "frögatan 181", "ltu"),
        Agent(world, "Spenus", "staregatan", "ltu"),
        Agent(world, "Gurke", "brännarvägen", "ica")
    ]

    for agent in agents:
        agent.start()

    #PYGAME
    cell_size = 32
    screen = pygame.display.set_mode((cell_size * world.width, cell_size * world.height))

    while True:

        for y in range(world.height):
            for x in range(world.width):
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                color = pygame.color.Color(255, 255, 255) if (x + y) % 2 == 0 else pygame.color.Color(200, 200, 200)
                pygame.draw.rect(screen, color, rect)

        for place in world.locations.values():
            rect = pygame.Rect(place[0] * cell_size + 3, place[1] * cell_size + 3, cell_size - 6, cell_size - 6)
            color = pygame.color.Color(255, 200, 200)
            pygame.draw.rect(screen, color, rect)

        for wall in world.graph.walls:
            rect = pygame.Rect(wall[0] * cell_size, wall[1] * cell_size, cell_size, cell_size)
            color = pygame.color.Color(0, 0, 0)
            pygame.draw.rect(screen, color, rect)

        pygame.display.update()
        world.step_forward(0.25)
        pygame.time.delay(100)