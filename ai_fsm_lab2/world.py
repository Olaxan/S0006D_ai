""" Represent a 2D world with agents and locations """

from enum import Enum, auto
from random import randint

from config import *
from path import Path, WeightedGrid
from telegram import Telegram


class TerrainTypes(Enum):
    Ground  = auto()
    Rock    = auto()
    Water   = auto()
    Swamp   = auto()
    Tree    = auto()

class Item(Enum):
    Tree    = auto()
    Stump   = auto()
    Ore     = auto()

class WorldGrid(WeightedGrid):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.terrain = [(TerrainTypes.Ground, 1, True)] * (width * height)
        self.items = []

    def cost(self, cell):
        x, y = cell
        return self.terrain[x + self.width * y][1]

    def is_free(self, cell):
        return self.cost(cell) != 0

    def set_terrain(self, cell, terrain, weight=1):
        x, y = cell
        t = self.get_terrain(cell)
        self.terrain[x + self.width * y] = (terrain, weight, t[2])

    def get_terrain(self, cell):
        x, y = cell
        return self.terrain[x + self.width * y]

    def set_fog(self, cell, fog):
        x, y = cell
        self.terrain[x + self.width * y][2] = fog

    def get_fog(self, cell):
        x, y = cell
        return self.terrain[x + self.width * y][2]

    def set_terrain_block(self, cell, size, terrain, weight=1, rand_count=None):
        x, y = cell
        r = range(size ** 2)

        if rand_count is not None:
            r = [randint(0, size ** 2) for i in range(rand_count)]

        for i in r:
            self.set_terrain((x + (i % size), y + (i // size)), terrain, weight)

def load_map(filename):
    try:
        file = open(filename, "r")
    except OSError:
        return None

    lines = file.readlines()
    file.close()
    height = len(lines)

    if height == 0:
        return False

    width = len(max(lines, key=len)) - 1

    grid = WorldGrid(width * WORLD_SCALE, height * WORLD_SCALE)

    y = 0
    for line in lines:
        x = 0
        for char in line:
            if char == 'B':
                grid.set_terrain_block((x * WORLD_SCALE, y * WORLD_SCALE), WORLD_SCALE, TerrainTypes.Rock, 0)
            elif char == 'G':
                grid.set_terrain_block((x * WORLD_SCALE, y * WORLD_SCALE), WORLD_SCALE, TerrainTypes.Swamp, 2)
            elif char == 'V':
                grid.set_terrain_block((x * WORLD_SCALE, y * WORLD_SCALE), WORLD_SCALE, TerrainTypes.Water, 0)
            elif char == 'T':
                grid.set_terrain_block((x * WORLD_SCALE, y * WORLD_SCALE), WORLD_SCALE, TerrainTypes.Tree, 0, WORLD_TREES_PER_CELL)
            x += 1
        y += 1

    return grid

class World:
    """ Class for holding locations,
    as well as managing agents in the world, and providing messaging """

    _next_id = 0        # Static ID counter

    def __init__(self, grid, locations=None, heuristic=None):
        self._messages = []
        self._time = 0
        self._graph = grid
        self.agents = {}
        self.heuristic = heuristic
        self.locations = locations if locations is not None else {}

    @classmethod
    def from_map(cls, filename, locations=None, heuristic=None):
        grid = load_map(filename)
        return cls(grid, locations, heuristic)

    @property
    def width(self) -> int:
        return self._graph.width

    @property
    def height(self) -> int:
        return self._graph.height

    @property
    def graph(self) -> WeightedGrid:
        return self._graph

    def _id_is_free(self, agent_id: int) -> bool:
        """Internal - check if ID is free"""
        return agent_id not in self.agents

    def _cell_is_free(self, cell) -> bool:
        """Internal - check if location cell is free"""
        return cell not in self.locations.values() and self.graph.is_free(cell)

    def _dispatch_delayed(self):
        """Internal - dispatch all due messages in queue"""
        for message in self._messages:
            if self._time >= message.dispatch_time:
                self.dispatch(message)
                self._messages.remove(message)

    def register_agent(self, agent) -> int:
        """Register an agent and call initializer, returning agent's assigned ID"""
        self.agents[self._next_id] = agent
        self._next_id += 1
        agent.init()
        return self._next_id - 1

    def remove_agent(self, agent_id: int):
        """Remove an agent from the dictionary"""
        if agent_id in self.agents: self.agents.pop(agent_id)

    def get_agent(self, agent_id: int):
        """Returns an agent when provided with valid ID"""
        return self.agents[agent_id] if agent_id in self.agents else None

    def get_agents(self, *agent_ids):
        """Return list of agents matching ID:s in args"""
        agents = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if agent is not None:
                agents.append(agent)
        return agents

    def get_location(self, name: str) -> (int, int):
        """Returns a location coordinate when provided with location string"""
        return self.locations.get(name, (0, 0))

    def get_random_cell(self):
        while True:
            cell = (randint(0, self.width - 1), randint(0, self.height - 1))
            if self._cell_is_free(cell):
                return cell

    def get_path(self, path_from, path_to):
        return Path.a_star_search(self.graph, path_from, path_to, self.heuristic)[:2]

    def place_random(self, *args):
        for place in args:
            self.locations[place] = self.get_random_cell()

    def is_at(self, agent, location: str) -> bool:
        """Returns whether the specified agent is present at a location string"""

        if isinstance(agent, int):
            agent = self.get_agent(agent)

        if agent is None:
            return False

        x, y = agent.location
        return (x, y) == self.locations[location]

    def step_forward(self, step=1):
        """Move the world forward a step of the specified size, update all agents"""

        self._time += step
        self._dispatch_delayed()

        for agent in self.agents.values():
            agent.update(step)

    def dispatch(self, telegram: Telegram, delay=0):
        """Dispatch a message with optional delay"""

        agents = []

        if telegram.receiver_id is None:
            for agent in self.agents.values():
                if agent.agent_id is not telegram.sender_id:
                    agents.append(agent)
        else:
            if isinstance(telegram.receiver_id, int):
                agent = self.get_agent(telegram.receiver_id)
                if agent is not None:
                    agents.append(agent)
            else:
                agents = self.get_agents(*telegram.receiver_id)

        if delay <= 0:
            for agent in agents:
                agent.handle_message(telegram)
            return len(agents)

        telegram.dispatch_time = self._time + delay
        self._messages.append(telegram)
        return 0
