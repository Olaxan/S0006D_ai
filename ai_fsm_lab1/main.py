import sys, time
from agent import Agent
from world import World

if __name__ == "__main__":

    locations = {
        "travven"       : [1, 1],
        "dallas"        : [3, 0],
        "coop"          : [5, 0],
        "brännarvägen"  : [2, 2],
        "morö backe"    : [3, 2],
        "frögatan 154"  : [3, 3],
        "frögatan 183"  : [3, 4],
        "ltu"           : [4, 4]
    }

    world = World(locations)

    agents = [
        Agent(world, "Semlo", "brännarvägen", "coop"),
        Agent(world, "Lukas", "morö backe", "dallas"),
        Agent(world, "Sahmon", "frögatan 183", "ltu"),
        Agent(world, "Spenus", "frögatan 154", "ltu"),
        Agent(world, "Gurke", "brännarvägen", "coop")
    ]

    for agent in agents:
        agent.start()

    while True:
        time.sleep(0.5)
        world.step_forward(0.25)