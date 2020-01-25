import agent

class World:

    _agents = {}
    _locations = {}
    _next_id = 0

    def __init__(self, locations: dict = {}):
        self._locations = locations

    def id_is_free(self, id: int):
        return id not in self._agents

    def register_agent(self, agent) -> int:
        self._agents[self._next_id] = agent
        self._next_id += 1
        return self._next_id - 1

    def remove_agent(self, id: int):
        if id in self._agents: self._agents.pop(id)

    def get_agent(self, id: int):
        return self._agents[id] if id in self._agents else None

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
        for agent in self._agents.values():
            agent.update()