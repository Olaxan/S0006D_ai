from __future__ import annotations
from abc import ABC, abstractmethod

class World:

    _agents = {}
    _locations = {}
    _next_id = 0

    def __init__(self, locations: dict = {}, agents: list = []):
        self._locations = locations
        for agent in agents:
            agent.world = self
            self.add_agent(agent)

    def id_is_free(self, id: int):
        return id not in self._agents

    def add_agent(self, agent: StateContext) -> int:
        agent.world = self
        agent.id = self._next_id
        agent.start()
        self._agents[self._next_id] = agent
        self._next_id += 1
        return agent.id

    def add_agents(self, *agents: StateContext):
        for a in agents:
            self.add_agent(a)

    def remove_agent(self, id: int):
        if id in self._agents: self._agents.pop(id)

    def get_agent(self, id: int) -> StateContext:
        return self._agents[id] if id in self._agents else None

    def add_location(self, name: str, coordinates: (int, int)):
        self._locations[name] = coordinates

    def remove_location(self, name: str):
        if name in self._locations: self._locations.pop(name)

    def get_location(self, name: str) -> (int, int):
        return self._locations[name] if name in self._locations else (0, 0)

    def is_at(self, id: int, location: str) -> bool:
        agent = self.get_agent(id)
        if agent == None: return False
        return agent.location == self._locations[location]

    def update(self):
        for agent in self._agents.values():
            agent.update()

class StateContext(ABC):

    _id = 0
    _location = [0, 0]
    _name = "Agent"
    _world = None
    _state = None

    def __init__(self, initial: State, name: str):
        self._name = name
        self._state = initial # agent will be "activated" by world manager

    def changeState(self, state: State):

        if self._state is not None and type(state) is not Goto:
            self._state.exit()

        self._state = state
        self.start()

    def start(self):
        if self._state is not None and self._world is not None:
            self._state.context = self
            self._state.enter()

    def update(self):
        self._state.execute()

    def is_at(self, location: str) -> bool:
        return self._world.is_at(self._id, location) if self._world != None else False

    def goto(self, location: str):
        current = self._state
        target = self.world.get_location(location)
        self.describe("going to %s for %s" % (location.capitalize(), current.state_name))
        self.changeState(Goto(target, current))

    def describe(self, action):
        print(self.name, "is", action)

    def say(self, phrase):
        print("%s: '%s'" % (self.name, phrase))

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, world: World):
        self._world = world

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def x(self):
        return self._location[0]

    @x.setter
    def x(self, value):
        self._location[0] = value

    @property
    def y(self):
        return self._location[1]

    @y.setter
    def y(self, value):
        self._location[1] = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location: [int, int]):
        self._location = location

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id: int):
        if self._world.id_is_free(id): self._id = id
        
class State(ABC):

    _context = None

    state_name = "unknown reasons"

    @property
    def context(self) -> StateContext:
        return self._context

    @context.setter
    def context(self, context: StateContext):
        self._context = context

    def enter(self):
        pass

    def execute(self):
        pass

    def exit(self):
        pass

class Goto(State):

    _target = [0, 0]
    _on_arrive: None

    def __init__(self, location: [int, int], on_arrive: State):
        self._on_arrive = on_arrive
        self._target = location

    def _has_arrived(self) -> bool:
        return self._target[0] == self.context.x and self._target[1] == self.context.y

    def execute(self):

        if self._has_arrived():
            self.context.changeState(self._on_arrive)
            return

        if self._target[0] < self.context.x: self.context.x -= 1
        elif self._target[0] > self.context.x: self.context.x += 1

        if self._target[1] < self.context.y: self.context.y -= 1
        elif self._target[1] > self.context.y: self.context.y += 1
