from __future__ import annotations

from enum import Enum, auto
from state import State, StateContext
from telegram import MessageTypes, Telegram
from world import World

class UnitTypes(Enum):
    Worker  = auto()
    Scout   = auto()

class Unit(StateContext):

    def __init__(self, world: World, unit_type, speed):
        super().__init__(WorkerState(), UnitGlobal())
        self._world = world
        self._location = [0, 0]
        self.speed = speed
        self.unit_type = unit_type

        self._id = self._world.register_agent(self)

    # Gets called by world manager, just before receiving an agent_id
    # For delayed initalization of variables that need reference to World
    def init(self):
        pass

    def on_move(self):
        pass

    @property   # Returns agent agent_id, immutable
    def agent_id(self):
        return self._id

    @property   # Returns agent World, immutable
    def world(self):
        return self._world

    @property
    def x(self):
        return self._location[0]

    @x.setter
    def x(self, value):
        self._location[0] = value
        self.on_move()

    @property
    def y(self):
        return self._location[1]

    @y.setter
    def y(self, value):
        self._location[1] = value
        self.on_move()

    @property   # Returns agent's [X, Y] position in World
    def location(self):
        return self.x, self.y

    @location.setter
    def location(self, location):
        self.x, self.y = location

    @property
    def is_walking(self) -> bool:
        return isinstance(self.state, GotoState)

class UnitGlobal(State):
    pass

class GotoState(State):

    revertable = False

    def __init__(self, target, on_arrive=None, on_fail=None):
        self._on_arrive = on_arrive
        self._on_fail = on_fail
        self._target = target
        self._path = []
        self._progress = 0

    @property
    def path(self):
        return self._path

    @property
    def valid(self):
        return len(self._path) > 0

    def _has_arrived(self, context) -> bool:
        """Check if agent has arrived at target"""
        return self._target[0] == context.x and self._target[1] == context.y

    def _finish(self, context):
        """Call once agent is finished with path, to change state appropriately"""
        if self._on_arrive is not None:
            context.change_state(self._on_arrive)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_PATH_DONE, context.location)
        context.world.dispatch(arrive_msg)

    def _abort(self, context):
        """Call if agent failed pathing, to revert states appropriately"""
        if self._on_fail is not None:
            context.change_state(self._on_fail)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_PATH_FAIL, context.location)
        context.world.dispatch(arrive_msg)

    def enter(self, context):
        success, self._path = context.world.get_path(context.location, self._target)
        if not success:
            self._abort(context)

    def execute(self, context, step):

        path_len = len(self._path)

        if path_len > 0:
            self._progress += context.speed * step
            if self._progress >= path_len:
                context.location = self._path[-1]
                self._finish(context)
            else:
                context.location = self._path[int(self._progress)]
        else:
            self._abort(context)

class PathErrorState(State):

    def enter(self, context):
        print("Agent is placed in a path error state!")

class WorkerState(State):
    pass

class Scout(Unit):

    def on_move(self):
        pass

class ScoutState(State):

    def enter(self, context):
        target = context.world.get_random_cell()
        context.world.get_path(context.location, target)

    def execute(self, context, step):
        """Gets called once every FSM update, with the specified step size"""

    def exit(self, context):
        """Gets called once when exiting the state"""

    def on_message(self, context, telegram) -> bool:
        """Gets called by the FSM when a message has been received"""
