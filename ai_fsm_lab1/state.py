from __future__ import annotations
from abc import ABC

# FSM context - provides FSM capabilities to objects inheriting from it
class StateContext(ABC):

    _global_state: State = None
    _current_state: State = None
    _previous_state: State = None

    @property
    def state(self) -> State:
        return self._current_state

    def __init__(self, initial_state: State, global_state: State):
        self._current_state = initial_state
        self._global_state = global_state

    # Change to a new state, optionally omitting exiting current state,
    # and preventing the new state from overwriting the current state "blip"
    def change_state(self, state: State, do_exit=True, revertable=True):

        if revertable:
            self._previous_state = self._current_state

        if self._current_state is not None and do_exit:
            self._current_state.exit(self)

        self._current_state = state
        self._current_state.enter(self)

    # Reverts the state machine to its previous state
    def revert_state(self):
        self.change_state(self._previous_state)

    # Check if the FSM is currently in a state of the provided type
    def is_in_state(self, state: State) -> bool:
        return isinstance(self._current_state, state)

    # Start the FSM, entering the current state
    def start(self):
        if self._current_state is not None:
            self._current_state.enter(self)

    # Moves the FSM ahead a step of specified size.
    # Step size is passed to update functions.
    def update(self, step = 1):
        if self._global_state is not None and not self._current_state.ignore_global: 
            self._global_state.execute(self, step)
        if self._current_state is not None: 
            self._current_state.execute(self, step)

    # Sends a message to the current state, or if not handled; the global state
    def handle_message(self, message):
        if self._current_state is not None and self._current_state.on_message(self, message):
            return True
        if self._global_state is not None and self._global_state.on_message(self, message):
            return True

# An FSM state, which can be provided to the StateContext FSM
class State(ABC):

    # Can be set to tell the global state to exit early.
    ignore_global = False

    # Gets called once while entering the state
    def enter(self, context):
        pass

    # Gets called once every FSM update, with the specified step size
    def execute(self, context, step):
        pass

    # Gets called once when exiting the state
    def exit(self, context):
        pass

    # Gets called by the FSM when a message has been received
    def on_message(self, context, telegram) -> bool:
        pass
