import sys, time
from state import World
from agent import Agent, IdleState

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

    world.add_agents(
        Agent("Henry", "staregatan", "coop"),
        Agent("Lukas", "villagatan", "dallas")
    )

    while True:
        time.sleep(2)
        world.update()