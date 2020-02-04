from __future__ import annotations
from abc import ABC, abstractmethod

class StateContext(ABC):

    _global_state:      State = None
    _current_state:     State = None
    _previous_state:    State = None

    def __init__(self, initial_state: State, global_state: State):
        self._current_state = initial_state
        self._global_state = global_state

    def change_state(self, state: State, do_exit: bool = True, revertable = True):

        if revertable:
            self._previous_state = self._current_state

        if self._current_state is not None and do_exit:
            self._current_state.exit(self)
        
        self._current_state = state
        self._current_state.enter(self)

    def revert_state(self):
        #print("Reverting from {} to {}".format(self._current_state, self._previous_state))
        self.change_state(self._previous_state)

    def is_in_state(self, state: State) -> bool:
        return type(self._current_state) == type(state)

    def start(self):
        if self._current_state is not None:
            self._current_state.enter(self)

    def init(self):
        pass

    def update(self, step = 1):
        if self._global_state is not None: self._global_state.execute(self, step)
        if self._current_state is not None: self._current_state.execute(self, step)

    def handle_message(self, message):
        if self._current_state is not None and self._current_state.on_message(self, message):
            return True
        if self._global_state is not None and self._global_state.on_message(self, message):
            return True

    @property
    def state(self) -> State:
        return self._current_state
        
class State(ABC):

    state_name = "unknown reasons"
    state_verb = "doing something"

    ignore_global = False

    def enter(self, context):
        pass

    def execute(self, context, step):
        pass

    def exit(self, context):
        pass

    def on_message(self, context, telegram) -> bool:
        return False
