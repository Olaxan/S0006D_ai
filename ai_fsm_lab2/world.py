""" Represent a 2D world with agents and locations """

from random import randint

from path import WeightedGrid, Path
from config import WORLD_SCALE, WORLD_TREES_PER_CELL
from telegram import Telegram

class WorldGrid(WeightedGrid):

    def __init__(self, width, height):
        super().__init__(width, height)
        self.water = []
        self.swamp = []
        self.trees = []

    def is_free(self, cell):
        return cell not in self.water and cell not in self.walls

    def add_block(self, to, cell, size, rand_count=None):
        x, y = cell
        r = range(size ** 2)

        if rand_count is not None:
            r = [randint(0, size ** 2) for i in range(rand_count)]

        for i in r:
            to.append((x + (i % size), y + (i // size)))

    def set_block(self, to, cell, size, value, rand_count=None):
        x, y = cell
        r = range(size ** 2)

        if rand_count is not None:
            r = [randint(0, size ** 2) for i in range(rand_count)]

        for i in r:
            to[(x + (i % size), y + (i // size))] = value

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
                grid.add_block(grid.walls, (x, y), WORLD_SCALE)
            elif char == 'G':
                grid.add_block(grid.swamp, (x, y), WORLD_SCALE)
                grid.set_block(grid.weights, (x, y), WORLD_SCALE, 2)
            elif char == 'V':
                grid.add_block(grid.water, (x, y), WORLD_SCALE)
            elif char == 'T':
                grid.add_block(grid.trees, (x, y), WORLD_SCALE, WORLD_TREES_PER_CELL)
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
    def time(self):
        """Returns the time as an hour decimal wrapped to 24 hours"""
        return ((self._time % 24) + 24) % 24

    @property
    def time_24(self) -> str:
        """Returns the time formatted as HH:MM"""
        return self.time_format_24(self._time)

    @property
    def hour_24(self) -> int:
        """Returns the current hour as an integer, in a 24 hour format"""
        return int(self._time % 24)

    @property
    def hour_12(self) -> (int, str):
        """Returns the current hour as an integer, in a 12 hour format, as well as AM or PM"""
        hour = int(self._time % 12)
        am = "AM" if self.time < 12 else "PM"
        return (hour, am)

    @property
    def minutes(self) -> int:
        """Returns the current number of minutes past the hour"""
        return int(60.0 * float(self._time % 1.0))

    @property
    def width(self) -> int:
        return self._graph.width

    @property
    def height(self) -> int:
        return self._graph.height

    @property
    def graph(self) -> WeightedGrid:
        return self._graph

    @staticmethod
    def time_format_24(time) -> str:
        """Formats a given time as HH:MM"""
        hour = int(time % 24)
        minute = int(60.0 * float(time % 1.0))
        return "{:02d}:{:02d}".format(hour, minute)

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

    def dispatch_scheduled(self, time, telegram: Telegram):
        """Set a message for scheduled dispatch, the current or next day"""
        if time < self.time:
            time += (24 - self.time)
        else:
            time -= self.time

        self.dispatch(telegram, time)
