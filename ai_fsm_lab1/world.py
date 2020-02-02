import agent
from telegram import Telegram

class World:

    _agents = {}
    _locations = {}
    _messages = []
    _next_id = 0
    _time = 0

    def __init__(self, locations: dict = {}):
        self._locations = locations
        self._agents = {}
        self._messages = []
        self._time = 0

    @property
    def time(self):
        return ((self._time % 24) + 24) % 24

    @property
    def time_24(self):
        return self.time_format_24(self._time)

    @property
    def hour_24(self) -> int:
        return int(self._time % 24)

    @property
    def hour_12(self) -> int:
        return int(self._time % 12)

    @property
    def minutes(self) -> int:
        return int(60.0 * float(self._time % 1.0))

    @staticmethod
    def time_format_24(time):
        hour = int(time % 24)
        minute = int(60.0 * float(time % 1.0))
        return "{:02d}:{:02d}".format(hour, minute)

    def _id_is_free(self, id: int):
        return id not in self._agents

    def _dispatch_delayed(self):
        for message in self._messages:
            if self._time >= message.dispatch_time:
                self.dispatch(0, message)
                self._messages.remove(message)

    def register_agent(self, agent) -> int:
        self._agents[self._next_id] = agent
        self._next_id += 1
        return self._next_id - 1

    def remove_agent(self, id: int):
        if id in self._agents: self._agents.pop(id)

    def get_agent(self, id: int):
        return self._agents[id] if id in self._agents else None

    def get_agents(self, *ids):
        agents = []
        for id in ids:
            agent = self.get_agent(id)
            if agent is not None: agents.append(agent)
        return agents

    def add_location(self, name: str, coordinates: (int, int)):
        self._locations[name] = coordinates

    def remove_location(self, name: str):
        if name in self._locations: self._locations.pop(name)

    def get_location(self, name: str) -> (int, int):
        return self._locations.get(name, [0, 0])

    def is_at(self, agent, location: str) -> bool:
        
        if type(agent) == int:
            agent = self.get_agent(id)
            
        if agent == None: return False
        return agent.location == self._locations[location]

    def step_forward(self, step = 1):
        self._time += step
        self._dispatch_delayed()

        for agent in self._agents.values():
            agent.update(step)

        print()

    def dispatch(self, delay, telegram: Telegram):

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
        else:
            telegram.dispatch_time = self._time + delay
            self._messages.append(telegram)

        #print("Message sent to %d recipients" % (len(agents)))

    def dispatch_scheduled(self, time, telegram: Telegram):
        if time < self.time:
            time += (24 - self.time)
            #print("[{}] adding {} to reach {}".format(self.time, 24 - self.time, time))
        else:
            time -= self.time

        self.dispatch(time, telegram)
        #print("Message delayed by {}".format(time))