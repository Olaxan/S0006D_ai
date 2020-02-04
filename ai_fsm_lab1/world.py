import agent
from telegram import Telegram

# Class for holding locations, as well as managing agents in the world, and providing messaging
class World:

    _agents = {}        # Agent dictionary, key is ID
    _locations = {}     # Location dictionary, key is location string
    _messages = []      # Delayed message queue
    _next_id = 0        # Static ID counter
    _time = 0           # Game time

    def __init__(self, locations: dict = {}):
        self._locations = locations
        self._agents = {}
        self._messages = []
        self._time = 0

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

    # Formats a given time as HH:MM
    @staticmethod
    def time_format_24(time) -> str:
        hour = int(time % 24)
        minute = int(60.0 * float(time % 1.0))
        return "{:02d}:{:02d}".format(hour, minute)

    # Internal - check if ID is free
    def _id_is_free(self, id: int):
        return id not in self._agents

    # Internal - dispatch all due messages in queue
    def _dispatch_delayed(self):
        for message in self._messages:
            if self._time >= message.dispatch_time:
                self.dispatch(message)
                self._messages.remove(message)

    # Register an agent and call initializer, returning agent's assigned ID
    def register_agent(self, agent) -> int:
        self._agents[self._next_id] = agent
        self._next_id += 1
        agent.init()
        return self._next_id - 1

    # Remove an agent from the dictionary
    def remove_agent(self, id: int):
        if id in self._agents: self._agents.pop(id)

    # Returns an agent when provided with valid ID
    def get_agent(self, id: int):
        return self._agents[id] if id in self._agents else None

    # Return list of agents matching ID:s in args
    def get_agents(self, *ids):
        agents = []
        for id in ids:
            agent = self.get_agent(id)
            if agent is not None: agents.append(agent)
        return agents

    # Adds a new location to the location dictionary
    def add_location(self, name: str, coordinates: (int, int)):
        self._locations[name] = coordinates

    # Removes a location from the location dictionary
    def remove_location(self, name: str):
        if name in self._locations: self._locations.pop(name)

    # Returns a location coordinate when provided with location string
    def get_location(self, name: str) -> (int, int):
        return self._locations.get(name, [0, 0])

    # Returns whether the specified agent is present at a location string
    def is_at(self, agent, location: str) -> bool:
        
        if type(agent) == int:
            agent = self.get_agent(id)
            
        if agent == None: return False
        return agent.location == self._locations[location]

    # Move the world forward a step of the specified size, update all agents
    def step_forward(self, step = 1):

        if self.time < step:
            print(" ===[ Day {} ]======================================================= ".format(int(self._time // 24)))

        if self._time % step == 0:
            print()

        self._time += step
        self._dispatch_delayed()

        for agent in self._agents.values():
            agent.update(step)

    # Dispatch a message with optional delay
    def dispatch(self, telegram: Telegram, delay = 0):

        agents = []

        if telegram.receiver_id == None:
            for agent in self._agents.values():
                if agent.id is not telegram.sender_id: agents.append(agent)
        else:
            if type(telegram.receiver_id) is int:
                agents.append(self.get_agent(telegram.receiver_id))
            else:
                agents = self.get_agents(*telegram.receiver_id)

        if delay <= 0:
            for agent in agents:
                agent.handle_message(telegram)

            #print("Message sent to {} agents".format(len(agents)))
            return len(agents)
        else:
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