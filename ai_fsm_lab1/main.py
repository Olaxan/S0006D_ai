import sys, time
from agent import Agent
from world import World

if __name__ == "__main__":

    locations = {
        "travven"       : [0, 0],
        "dallas"        : [3, 0],
        "coop"          : [5, 0],
        "staregatan"    : [2, 2],
        "villagatan"    : [3, 2],
        "ltu"           : [4, 4]
    }

    world = World(locations)

    agents = [
        Agent(world, "Henry", "staregatan", "coop"),
        Agent(world, "Lukas", "villagatan", "dallas")
    ]

    for agent in agents:
        agent.start()

    while True:
        time.sleep(2)
        world.update()