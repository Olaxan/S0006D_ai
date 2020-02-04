import sys, time
from agent import Agent
from world import World

if __name__ == "__main__":

    locations = {
        "travven"       : [1, 1],
        "dallas"        : [3, 0],
        "coop"          : [5, 0],
        "staregatan"    : [2, 2],
        "villagatan"    : [3, 2],
        "frögatan 154"  : [3, 3],
        "frögatan 183"  : [3, 4],
        "ltu"           : [4, 4]
    }

    world = World(locations)

    agents = [
        Agent(world, "Henry", "staregatan", "coop"),
        Agent(world, "Lukas", "villagatan", "dallas"),
        Agent(world, "Sahmon", "frögatan 183", "ltu"),
        Agent(world, "Bulifer", "frögatan 154", "ltu"),
        Agent(world, "Jenny", "staregatan", "coop")
    ]

    for agent in agents:
        agent.start()

    while True:
        time.sleep(0.2)
        world.step_forward(0.25)