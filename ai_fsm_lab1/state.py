from __future__ import annotations
from abc import ABC, abstractmethod

class StateContext(ABC):

    _global_state:      State = None
    _current_state:     State = None
    _previous_state:    State = None

    def __init__(self, initial_state: State, global_state: State):
        self._current_state = initial_state
        self._global_state = global_state

    def change_state(self, state: State, do_exit: bool = True):

        self._previous_state = self._current_state

        if self._current_state is not None and do_exit:
            self._current_state.exit()
        
        self._current_state = state
        self.start()

    def revert_state(self):
        #print("reverting from %s to %s" % (self._current_state, self._previous_state))
        self.change_state(self._previous_state)

    def is_in_state(self, state: State) -> bool:
        return type(self._current_state) == type(state)

    def init(self):
        pass

    def start(self):
        if self._current_state is not None:
            self._current_state.context = self
            self._current_state.enter()
        if self._global_state is not None:
            self._global_state.context = self

    def update(self, step = 1):
        if self._global_state is not None: self._global_state.execute(step)
        if self._current_state is not None: self._current_state.execute(step)

    def handle_message(self, message):
        if self._current_state is not None and self._current_state.on_message(message):
            return True
        if self._global_state is not None and self._global_state.on_message(message):
            return True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def state(self) -> State:
        return self._current_state
        
class State(ABC):

    _context = None

    state_name = "unknown reasons"
    state_verb = "doing something"

    ignore_global = False

    @property
    def context(self) -> StateContext:
        return self._context

    @context.setter
    def context(self, context: StateContext):
        self._context = context

    def on_message(self, telegram) -> bool:
        return False

    def enter(self):
        pass

    def execute(self, step):
        pass

    def exit(self):
        pass
