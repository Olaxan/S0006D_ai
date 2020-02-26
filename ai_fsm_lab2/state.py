from __future__ import annotations
from abc import ABC

class StateContext(ABC):
    """FSM context - provides FSM capabilities to objects inheriting from it"""

    _global_state: State = None
    _current_state: State = None
    _previous_state: State = None

    @property
    def state(self) -> State:
        return self._current_state

    def __init__(self, initial_state: State, global_state: State):
        self._current_state = initial_state
        self._global_state = global_state

    def change_state(self, state: State, do_exit=True):
        """Change to a new state, optionally omitting exiting current state,
        and preventing the new state from overwriting the current state "blip"""

        if self._current_state.revertable:
            self._previous_state = self._current_state

        if self._current_state is not None and do_exit:
            self._current_state.exit(self)

        self._current_state = state
        self._current_state.enter(self)

    def revert_state(self):
        """Reverts the state machine to its previous state"""
        self.change_state(self._previous_state)

    def is_in_state(self, state: State) -> bool:
        """Check if the FSM is currently in a state of the provided type"""
        return isinstance(self._current_state, state)

    def start(self):
        """Start the FSM, entering the current state"""
        if self._current_state is not None:
            self._current_state.enter(self)

    def update(self, step = 1):
        """Moves the FSM ahead a step of specified size.
        Step size is passed to update functions."""
        if self._global_state is not None and not self._current_state.ignore_global:
            self._global_state.execute(self, step)
        if self._current_state is not None:
            self._current_state.execute(self, step)

    def handle_message(self, message):
        """Sends a message to the current state, or if not handled; the global state"""
        if self._current_state is not None and self._current_state.on_message(self, message):
            return True
        if self._global_state is not None and self._global_state.on_message(self, message):
            return True

class State(ABC):
    """An FSM state, which can be provided to the StateContext FSM"""

    # Can be set to tell the global state to exit early.
    ignore_global = False

    # Set to false if the state is temporary, and should not be saved in previous state variable
    revertable = True

    def enter(self, context):
        """Gets called once while entering the state"""

    def execute(self, context, step):
        """Gets called once every FSM update, with the specified step size"""

    def exit(self, context):
        """Gets called once when exiting the state"""

    def on_message(self, context, telegram) -> bool:
        """Gets called by the FSM when a message has been received"""
