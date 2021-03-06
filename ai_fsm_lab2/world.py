""" Represent a 2D world with agents and locations """

import threading
from collections import defaultdict
from queue import Queue
from copy import deepcopy
from enum import Enum, auto
from random import randint

from config import *
from path import Path, WeightedGrid
from telegram import Telegram


class TerrainTypes(Enum):
    """Represents different types of terrain in the world"""
    Void    = auto()
    Ground  = auto()
    Rock    = auto()
    Water   = auto()
    Swamp   = auto()
    Tree    = auto()
    Stump   = auto()

class ResourceTypes(Enum):
    """Represents various resources for building and crafting"""
    Log     = auto()
    Coal    = auto()

class BuildingTypes(Enum):
    """Represents a few types of buildings that can be constructed,
    as well as holding the construction data"""
    Camp        = auto()
    Buildsite   = auto()
    Kiln        = (ResourceTypes.Log, BUILD_KILN_LOGS, BUILD_KILN_TIME)

class PathMode(Enum):
    """Represents pathfinding modes"""
    AStar       = auto()
    Dijkstra    = auto()

class WorldGrid(WeightedGrid):

    def __init__(self, width, height):
        super().__init__(width, height)
        self.terrain = [deepcopy([TerrainTypes.Ground, 1, HAS_FOG]) for x in range(width * height)]
        self.on_terrain_changed = []

    def cost(self, cell):

        if cell in self.weights:
            return self.weights[cell]

        t = self.get_tile(cell)
        return t[1] if t is not None else 0

    def is_free(self, cell):
        return self.cost(cell) != 0 and cell not in self.walls

    def get_tile(self, cell):

        x, y = cell
        if self.is_in_bounds(cell):
            return self.terrain[x + self.width * y]

        return None

    def set_tile(self, cell, terrain, weight=None):

        t = self.get_tile(cell)

        if t is None:
            return

        t[0] = terrain
        if weight is not None:
            t[1] = weight

        for event in self.on_terrain_changed:
            event(cell, terrain)

    def get_terrain(self, cell):
        t = self.get_tile(cell)
        return t[0] if t is not None else None

    def set_fog(self, cell, fog):
        t = self.get_tile(cell)
        if t is not None:
            t[2] = fog

    def get_fog(self, cell):
        t = self.get_tile(cell)
        return t[2] if t is not None else True

    def set_terrain_block(self, cell, size, terrain, weight=1, rand_count=None):
        x, y = cell

        if rand_count is not None and size != 1:
            r = [randint(0, size ** 2) for i in range(rand_count)]
        else:
            r = range(size ** 2)

        for i in r:
            self.set_tile((x + (i % size), y + (i // size)), terrain, weight)

def load_map(filename):
    """Load a map from a file"""

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
            cell = (x * WORLD_SCALE, y * WORLD_SCALE)
            if char == 'B':
                grid.set_terrain_block(cell, WORLD_SCALE, TerrainTypes.Rock, 0)
            elif char == 'G':
                grid.set_terrain_block(cell, WORLD_SCALE, TerrainTypes.Swamp, 2)
            elif char == 'V':
                grid.set_terrain_block(cell, WORLD_SCALE, TerrainTypes.Water, 0)
            elif char == 'T':
                grid.set_terrain_block(cell, WORLD_SCALE, TerrainTypes.Tree, 2, WORLD_TREES_PER_CELL)
            x += 1
        y += 1

    return grid

class World:
    """ Class for holding locations,
    as well as managing agents in the world, and providing messaging """

    _next_id = 0        # Static ID counter

    def __init__(self, grid):
        self._messages = []
        self._time = 0
        self._graph = grid
        self.agents = {}
        self.buildings = {}
        self.resources = defaultdict(lambda: defaultdict(int))

        self.path_queue = Queue()
        self.path_thread = threading.Thread(target=self.do_path)
        self.path_thread.start()

        self.on_buildings_changed = []
        self.on_resources_changed = []

    @classmethod
    def from_map(cls, filename):
        grid = load_map(filename)
        return cls(grid)

    @property
    def width(self) -> int:
        return self._graph.width

    @property
    def height(self) -> int:
        return self._graph.height

    @property
    def graph(self) -> WorldGrid:
        return self._graph

    @property
    def all_agents(self):
        return self.agents.values()

    def _id_is_free(self, agent_id: int) -> bool:
        """Internal - check if ID is free"""
        return agent_id not in self.agents

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
        if agent_id in self.agents:
            self.agents.pop(agent_id)

    def get_agent(self, agent_id):
        """Returns an agent when provided with valid ID"""
        return self.agents.get(agent_id, None)

    def get_agents(self, agent_ids):
        """Return list of agents matching ID:s in args"""
        agents = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if agent is not None:
                agents.append(agent)
        return agents

    def get_agents_in_state(self, state, count=None):
        """Returns a list of agents in a particular state (or substate)"""

        agents = list(filter(lambda L: isinstance(L.state, state), self.all_agents))

        if len(agents) == 0:
            return None
        if count == 1:
            return agents[0]
        if count is None:
            return agents

        return agents[:min(count, len(agents))]

    def get_random_cell(self, origin=None, radius=10):
        """Gets a random cell in the world, or around a specific point"""

        while True:
            if origin is None:
                cell = (randint(0, self.width - 1), randint(0, self.height - 1))
            else:
                o_x, o_y = origin
                cell = (o_x + randint(-radius, radius), o_y + randint(-radius, radius))

            if self.graph.is_in_bounds(cell) and self.graph.is_free(cell) and cell not in self.buildings:
                return cell

    def do_path(self):
        """Runs in a separate thread to handle path queries from game agents"""

        while True:
            query = self.path_queue.get(block=True)

            fog_filter = None if query[4] else lambda cell: not self.graph.get_fog(cell)

            if query[0] == PathMode.AStar:
                Path.a_star_proxy(self.graph, query[1], query[2], query[3], filter_func=fog_filter, heuristic=Path.diagonal)
            elif query[0] == PathMode.Dijkstra:
                Path.dijkstras_proxy(self.graph, query[1], query[2], query[3], filter_func=fog_filter)

    def path(self, path_from, path_to, on_finish, path_through_fog=False):
        """Calculates an A* path and runs on_finish with the path data"""

        query = (PathMode.AStar, path_from, path_to, on_finish, path_through_fog)
        self.path_queue.put(query)

    def path_nearest_resource(self, path_from, item_type, on_finish, path_through_fog=False, exclude=None):
        """Calculates an path to the nearest resource of a specific type,
         and runs on_finish with the path data"""

        if exclude is None:
            exclude = []

        if item_type not in self.resources:
            on_finish(False, None)

        goal = lambda cell: self.get_resource(cell, item_type) > 0 and cell not in exclude
        query = (PathMode.Dijkstra, path_from, goal, on_finish, path_through_fog)
        self.path_queue.put(query)

    def path_nearest_terrain(self, path_from, terrain_type, on_finish, path_through_fog=False, exclude=None):
        """Calculates an path to the nearest block of a specific terrain type,
         and runs on_finish with the path data"""

        if exclude is None:
            exclude = []

        goal = lambda cell: self.graph.get_terrain(cell) == terrain_type and cell not in exclude
        query = (PathMode.Dijkstra, path_from, goal, on_finish, path_through_fog)
        self.path_queue.put(query)

    def path_nearest_fog(self, path_from, on_finish):
        """Calculates an path to the nearest block with fog-of-war,
         and runs on_finish with the path data"""

        query = (PathMode.Dijkstra, path_from, self.graph.get_fog, on_finish, None)
        self.path_queue.put(query)

    def reveal(self, cell):
        """Removes fog-of-war in a 3x3 pattern around the specified cell,
        and returns a list of the newly discovered cells"""

        discovered = []
        self.graph.set_fog(cell, False)
        neighbours = self.graph.neighbours(cell, False)
        for n in neighbours:
            if self.graph.get_fog(n):
                self.graph.set_fog(n, False)
                discovered.append(n)

        return discovered

    def add_location(self, location, location_type):
        """Adds a building to the location dictionary"""

        self.buildings[location] = location_type

        for event in self.on_buildings_changed:
            event(location, location_type)

    def get_locations(self, location_type):
        """Gets a list of all buildings of the specified type,
        or None if none were found"""

        locations = []
        for key in self.buildings:
            if self.buildings[key] is location_type:
                locations.append(key)

        return locations if len(locations) > 0 else None

    def add_resource(self, location, resource, count=1):
        """Adds resources to the specified cell"""

        self.resources[resource][location] += count
        c = self.resources[resource][location]

        if c == 0:
            self.resources[resource].pop(location)

        for event in self.on_resources_changed:
            event(location, resource, c)

        return c

    def get_resource(self, location, resource):
        """Gets the number of resources of a specific type at a cell"""

        if location in self.resources[resource]:
            return self.resources[resource][location]

        return 0

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
                agents = self.get_agents(telegram.receiver_id)

        if delay <= 0:
            for agent in agents:
                agent.handle_message(telegram)
            return len(agents)

        telegram.dispatch_time = self._time + delay
        self._messages.append(telegram)
        return 0
