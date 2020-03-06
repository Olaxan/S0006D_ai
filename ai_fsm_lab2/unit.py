from __future__ import annotations
from random import randint

from enum import Enum, auto
from state import State, StateContext
from telegram import MessageTypes, Telegram
from world import World
from config import *

class UnitTypes(Enum):
    Worker  = auto()
    Scout   = auto()

class Unit(StateContext):

    def __init__(self, world: World, location, state):
        super().__init__(state(), UnitGlobal())
        self._world = world
        self._location = list(location)
        self.speed = UNIT_SPEED

        self._id = self._world.register_agent(self)

    # Gets called by world manager, just before receiving an agent_id
    # For delayed initalization of variables that need reference to World
    def init(self):
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

    @property
    def y(self):
        return self._location[1]

    @y.setter
    def y(self, value):
        self._location[1] = value

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
            for i in range(context.speed):
                cost = context.world.graph.cost(context.location)
                self._progress += context.speed / cost
                if self._progress < path_len:
                    context.location = self._path[int(self._progress)]
                else:
                    context.location = self._path[-1]
                    self._finish(context)
        else:
            self._abort(context)

class PathErrorState(State):

    def enter(self, context):
        print("Agent is placed in a path error state!")

class ManagerState(State):

    def enter(self, context):
        scouts = self.get_workers(context.world, INIT_SCOUT)
        for scout in scouts:
            scout_state = ScoutState()
            scout.change_state(TrainingState(None, TRAIN_TIME_SCOUT, scout_state))

    def get_workers(self, world, count):
        agents = list(filter(lambda L: isinstance(L.state, WorkerState), world.all_agents))
        return agents[:min(count, len(agents))]

class TrainingState(State):

    def __init__(self, location, time, after_train):
        self.location = location
        self.after_train = after_train
        self.time = time

    def enter(self, context):
        if self.location is not None: #TODO: Not working
            target = context.world.get_location()
            goto = GotoState(target, self)
            context.change_state(goto, False)

    def execute(self, context, step):
        self.time -= step
        if self.time <= 0:
            context.change_state(self.after_train)

class WorkerState(State):
    pass

class ScoutState(GotoState):

    def __init__(self):
        super().__init__(None)
        self.waiting = False

    def enter(self, context):
        self.waiting = True

    def get_random_path(self, context):
        self._progress = 0
        while True:
            self._target = context.world.get_random_cell()
            success, self._path = context.world.get_path(context.location, self._target)
            if success:
                break

    def _finish(self, context):
        self.waiting = True

    def _abort(self, context):
        self.waiting = True

    def execute(self, context, step):
        if self.waiting:
            if randint(0, 60) == 1:
                self.waiting = False
                self.get_random_path(context)
        else:
            super().execute(context, step)
            cells = context.world.reveal(context.location)
