from __future__ import annotations
from abc import ABC, abstractmethod

class StateContext(ABC):

    _global_state:      State = None
    _current_state:     State = None
    _previous_state:    State = None

    def __init__(self, initial_state: State, global_state: State, name: str):
        self._name = name
        self._current_state = initial_state
        self._global_state = global_state

    def change_state(self, state: State, do_exit: bool = True):

        self._previous_state = self._current_state

        if self._current_state is not None and do_exit:
            self._current_state.exit()
        
        self._current_state = state
        self.start()

    def revert_state(self):
        self.change_state(self._previous_state)

    def is_in_state(self, state: State) -> bool:
        return type(self._current_state) == type(state)

    def start(self):
        if self._current_state is not None:
            self._current_state.context = self
            self._current_state.enter()

    def update(self):
        if self._global_state is not None: self._global_state.execute()
        if self._current_state is not None: self._current_state.execute()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name
        
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

    def __init__(self, location: [int, int], on_arrive: State = None):
        self._on_arrive = on_arrive
        self._target = location

    def _has_arrived(self) -> bool:
        return self._target[0] == self.context.x and self._target[1] == self.context.y

    def execute(self):

        if self._has_arrived():
            self.context.change_state(self._on_arrive) if self._on_arrive is not None else self.context.revert_state()
            return

        if self._target[0] < self.context.x: self.context.x -= 1
        elif self._target[0] > self.context.x: self.context.x += 1

        if self._target[1] < self.context.y: self.context.y -= 1
        elif self._target[1] > self.context.y: self.context.y += 1
