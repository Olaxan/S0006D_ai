import agent, time
from telegram import Telegram

class World:

    _agents = {}
    _locations = {}
    _messages = []
    _next_id = 0

    def __init__(self, locations: dict = {}):
        self._locations = locations

    def _id_is_free(self, id: int):
        return id not in self._agents

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
            if agent is not None: agents.insert(agent)
        return agents

    def add_location(self, name: str, coordinates: (int, int)):
        self._locations[name] = coordinates

    def remove_location(self, name: str):
        if name in self._locations: self._locations.pop(name)

    def get_location(self, name: str) -> (int, int):
        return self._locations[name] if name in self._locations else (0, 0)

    def is_at(self, agent, location: str) -> bool:
        
        if type(agent) == int:
            agent = self.get_agent(id)
            
        if agent == None: return False
        return agent.location == self._locations[location]

    def update(self):
        self.dispatch_delayed()

        for agent in self._agents.values():
            agent.update()

    def dispatch(self, delay, telegram: Telegram):

        agents = []

        if telegram.receiver_id == None:
            for agent in self._agents.values():
                if agent.id is not telegram.sender_id: agents.append(agent)
        else:
            agents = self.get_agents(*telegram.receiver_id)

        if delay <= 0:
            for agent in agents:
                agent.handle_message(telegram)
        else:
            telegram.dispatch_time = time.time + delay
            self._messages.insert(telegram)

        #print("Message sent to %d recipients" % (len(agents)))

    def dispatch_delayed(self):
        for message in self._messages:
            if time.time >= message.dispatch_time:
                self.dispatch(0, message)
                self._messages.remove(message)