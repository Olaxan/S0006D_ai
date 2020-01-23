from __future__ import annotations
from abc import ABC, abstractmethod

class StateContext(ABC):

    _id = 0
    _name = "Agent"
    _location = [0, 0]
    _state = None

    def __init__(self, initial: State, id: int, name: str):
        self._id = id
        self._name = name
        self.changeState(initial)

    def changeState(self, state: State):
        if (self._state != None):
            self._state.exit()

        self._state = state
        self._state.context = self
        self._state.enter()

    def update(self):
        self._state.execute()

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
    
        
class State(ABC):

    _context = None

    @property
    def context(self) -> StateContext:
        return self._context

    @context.setter
    def context(self, context: StateContext):
        self._context = context

    def describe(self, *action):
        print(self.context.name, "is", action)

    def enter(self):
        pass

    def execute(self):
        pass

    def exit(self):
        pass

