from telegram import Telegram
from path import WeightedGrid
from random import randint

def load_map(filename):
    try:
        file = open(filename, "r")
    except OSError:
        return None

    lines = file.readlines()
    file.close()
    height = len(lines)
    walls = []

    if height == 0: 
        return False

    width = len(max(lines, key=len)) - 1

    y = 0
    for line in lines:
        x = 0
        for char in line:
            if   char == 'X':
                walls.append((x, y))
            elif char == 'S':
                start = (x, y)
            elif char == 'G':
                goal = (x, y)
            x += 1
        y += 1

    return width, height, walls, start, goal

# Class for holding locations, as well as managing agents in the world, and providing messaging
class World:

    _next_id = 0        # Static ID counter

    def __init__(self, width, height, walls=None, locations=None):
        self._messages = []
        self._time = 0
        self._graph = WeightedGrid(width, height, walls)
        self.agents = {}
        self.locations = locations if locations is not None else {}

    @classmethod
    def from_map(cls, filename, locations=None):
        width, height, walls = load_map(filename)[:3]
        return cls(width, height, walls, locations)

    # Returns the time as an hour decimal wrapped to 24 hours
    @property
    def time(self):
        return ((self._time % 24) + 24) % 24

    # Returns the time formatted as HH:MM
    @property
    def time_24(self) -> str:
        return self.time_format_24(self._time)

    # Returns the current hour as an integer, in a 24 hour format
    @property
    def hour_24(self) -> int:
        return int(self._time % 24)

    # Returns the current hour as an integer, in a 12 hour format, as well as AM or PM
    @property
    def hour_12(self) -> (int, str):
        hour = int(self._time % 12)
        am = "AM" if self.time < 12 else "PM"
        return (hour, am)

    # Returns the current number of minutes past the hour
    @property
    def minutes(self) -> int:
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

    # Formats a given time as HH:MM
    @staticmethod
    def time_format_24(time) -> str:
        hour = int(time % 24)
        minute = int(60.0 * float(time % 1.0))
        return "{:02d}:{:02d}".format(hour, minute)

    # Internal - check if ID is free
    def _id_is_free(self, agent_id: int) -> bool:
        return agent_id not in self.agents

    # Internal - check if location cell is free
    def _cell_is_free(self, cell) -> bool:
        return cell not in self.locations.values() and self.graph.is_free(cell)

    # Internal - dispatch all due messages in queue
    def _dispatch_delayed(self):
        for message in self._messages:
            if self._time >= message.dispatch_time:
                self.dispatch(message)
                self._messages.remove(message)

    # Register an agent and call initializer, returning agent's assigned ID
    def register_agent(self, agent) -> int:
        self.agents[self._next_id] = agent
        self._next_id += 1
        agent.init()
        return self._next_id - 1

    # Remove an agent from the dictionary
    def remove_agent(self, agent_id: int):
        if agent_id in self.agents: self.agents.pop(agent_id)

    # Returns an agent when provided with valid ID
    def get_agent(self, agent_id: int):
        return self.agents[agent_id] if agent_id in self.agents else None

    # Return list of agents matching ID:s in args
    def getagents(self, *agent_ids):
        agents = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if agent is not None:
                agents.append(agent)
        return agents

    # Returns a location coordinate when provided with location string
    def get_location(self, name: str) -> (int, int):
        return self.locations.get(name, (0, 0))

    def get_random_cell(self):
        while True:
            cell = (randint(0, self.width - 1), randint(0, self.height - 1))
            if self._cell_is_free(cell):
                return cell

    def place_random(self, *args):
        for place in args:
            self.locations[place] = self.get_random_cell()

    # Returns whether the specified agent is present at a location string
    def is_at(self, agent, location: str) -> bool:
        
        if isinstance(agent, int):
            agent = self.get_agent(agent)
            
        if agent is None:
            return False

        x, y = agent.location
        return (x, y) == self.locations[location]

    # Move the world forward a step of the specified size, update all agents
    def step_forward(self, step = 1):

        if self.time < step:
            print("\n ===[ Day {} ]======================================================= ".format(int(self._time // 24)))

        if self._time % step == 0:
            print()

        self._time += step
        self._dispatch_delayed()

        for agent in self.agents.values():
            agent.update(step)

    # Dispatch a message with optional delay
    def dispatch(self, telegram: Telegram, delay=0):

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
                agents = self.getagents(*telegram.receiver_id)

        if delay <= 0:
            for agent in agents:
                agent.handle_message(telegram)
            return len(agents)

        telegram.dispatch_time = self._time + delay
        self._messages.append(telegram)
        return 0

    # Set a message for scheduled dispatch, the current or next day
    def dispatch_scheduled(self, time, telegram: Telegram):
        if time < self.time:
            time += (24 - self.time)
        else:
            time -= self.time

        self.dispatch(telegram, time)