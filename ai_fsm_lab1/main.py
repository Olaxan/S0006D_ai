import sys
from agent import Agent, IdleState

if __name__ == "__main__":

    miner = Agent(0, "Henry", (10, 10))

    while 1:
        miner.update()