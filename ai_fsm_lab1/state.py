from __future__ import annotations
from abc import ABC, abstractmethod

class StateContext(ABC):

    _id = 0
    _state = None

    def __init__(self, initial: State, id: int) -> None:
        self._id = id
        self.changeState(initial)

    def changeState(self, state: State) -> None:
        if (self._state != None):
            self._state.exit()

        self._state = state
        self._state.context = self
        self._state.enter()

    def update(self) -> None:
        self._state.execute()
    
        
class State(ABC):

    _context = None

    @property
    def context(self) -> StateContext:
        return self._context

    @context.setter
    def context(self, context: StateContext) -> None:
        self._context = context

    @abstractmethod
    def enter(self):
        print("Agent entering state")

    @abstractmethod
    def execute(self):
        print("Agent update")

    @abstractmethod
    def exit(self):
        print("Agent exiting state")

