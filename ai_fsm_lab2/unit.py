from __future__ import annotations
from random import randint

from enum import Enum, auto
from state import State, StateContext
from telegram import MessageTypes, Telegram
from world import World, TerrainTypes, BuildingTypes, ResourceTypes
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
        # make camp where manager stands
        context.world.add_location(BuildingTypes.Camp, context.location)

        # create initial scouts
        worker_pool = context.world.get_agents_in_state(WorkerState, INIT_SCOUT)

        for scout in worker_pool:
            scout_state = ScoutState()
            scout.change_state(TrainingState(None, TIME_TRAIN_SCOUT, scout_state))

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_BUILDING_NEEDED:
            print("Yeah, yeah, I'll get it sorted")
            builder = context.world.get_agents_in_state(BuilderState, 1)
            if builder is None:

                trainees = context.world.get_agents_in_state(TrainingState)

                if trainees is not None:
                    trainees = list(filter(lambda L: L.after_train is BuilderState, trainees))

                    if len(trainees) > 0:
                        print("I'll put my best man on it! Once he's done training...")
                        first = trainees[0]
                        build_msg = Telegram(context.agent_id, first.agent_id, MessageTypes.MSG_BUILDING_NEEDED, telegram.data)
                        context.world.dispatch(build_msg, first.time + 1)
                        return

                print("Oops, ain't got no builders...")
                builder_state = BuilderState()
                worker = context.world.get_agents_in_state(WorkerState, 1)
                if worker is not None:
                    worker.change_state(TrainingState(None, TIME_TRAIN_BUILDER, builder_state))
                    build_msg = Telegram(context.agent_id, worker.agent_id, MessageTypes.MSG_BUILDING_NEEDED, telegram.data)
                    context.world.dispatch(build_msg, TIME_TRAIN_BUILDER + 1)
                else:
                    print("And no workers, either! Fuck me!")
            else:
                build_msg = Telegram(context.agent_id, builder.agent_id, MessageTypes.MSG_BUILDING_NEEDED, telegram.data)
                context.world.dispatch(build_msg)

class TrainingState(State):

    def __init__(self, location_type, time, after_train):
        self.begun = False
        self.location_type = location_type
        self.after_train = after_train
        self.time = time

    def check_building(self, context):
        target = context.world.get_locations(self.location_type)
        if target is None:
            print("Need a {} to train for this!".format(self.location_type))
            manager = context.world.get_agents_in_state(ManagerState, 1)
            build_msg = Telegram(context.agent_id, manager.agent_id, MessageTypes.MSG_BUILDING_NEEDED, self.location_type)
            context.world.dispatch(build_msg)
        else:
            goto = GotoState(target[0], self)
            context.change_state(goto, False)
            self.begun = True

    def enter(self, context):
        print("Training to become a", type(self.after_train))
        if self.location_type is None:
            self.begun = True
        else:
            self.check_building(context)

    def execute(self, context, step):
        if self.begun:
            self.time -= step
            if self.time <= 0:
                context.change_state(self.after_train)

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_BUILDING_DONE and telegram.data is self.location_type:
            self.check_building(context)
            return True

class BuilderState(State):

    def __init__(self):
        self.is_building = False

    def enter(self, context):
        if self.is_building:
            res = context.world.get_resource(context.location, ResourceTypes.Log)
            if res < BUILD_KILN_LOGS:
                resource_msg = Telegram(context.agent_id, None, MessageTypes.MSG_RESOURCE_NEEDED, (ResourceTypes.Log, context.location))
                context.world.dispatch(resource_msg)

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_BUILDING_NEEDED:
            print("Sure thing, boss!")
            camp_location = context.world.get_locations(BuildingTypes.Camp)
            build_origin = camp_location[0] if camp_location is not None else context.location
            build_site = context.world.get_random_cell(build_origin, 2)
            context.world.reveal(build_site)
            goto = GotoState(build_site, self)
            context.change_state(goto)
            self.is_building = True
            return

class WorkerState(State):

    def on_message(self, context, telegram):
        if telegram.message is MessageTypes.MSG_RESOURCE_FOUND:
            res, cell = telegram.data
            if res is TerrainTypes.Tree:
                print("Coming to chop it down!")
                state = WorkerLoggerState(cell)
                context.change_state(state)
                return True

        if telegram.message is MessageTypes.MSG_RESOURCE_NEEDED:
            res, cell = telegram.data


class WorkerLoggerState(WorkerState):

    def __init__(self, cell):
        self._target = cell
        self._timer = TIME_CHOP_TREE

    def enter(self, context):
        if context.location != self._target:
            context.change_state(GotoState(self._target, self))
            return

        print("Time to get a-choppin'!")

    def execute(self, context, step):
        self._timer -= step
        if self._timer <= 0:
            print("Finished chopping!")
            context.world.graph.set_terrain(self._target, TerrainTypes.Stump)
            context.world.add_resource(context.location, ResourceTypes.Log)
            camp = context.world.get_locations(BuildingTypes.Camp)
            if camp is not None:
                print("Guess I'll carry this to the camp.")
                state = WorkerTransportState(context.location, camp[0])
                context.change_state(state)
            else:
                print("I'll just leave this here, I suppose")
                context.change_state(WorkerState())

    def on_message(self, context, telegram):
        return False

class WorkerTransportState(WorkerState):

    def __init__(self, from_tile, to_tile, resource=None, count=1):
        self._resource = resource
        self._from_tile = from_tile
        self._to_tile = to_tile
        self._count = count
        self._is_carrying = False

    def enter(self, context):
        if self._is_carrying and context.location == self._to_tile:
            count = context.world.add_resource(context.location, self._resource)
            if count < self._count:
                goto = GotoState(self._from_tile, self)
                context.change_state(goto)
                return
            else:
                context.change_state(WorkerState())
                return

        if context.location == self._from_tile:
            if context.world.get_resource(context.location, self._resource) > 0:
                self._is_carrying = True
                goto = GotoState(self._to_tile, self)
                context.change_state(goto)
            else:
                print("Nothing more to carry! Well, nothing doing...")
                context.change_state(WorkerState())

    def on_message(self, context, telegram):
        return False

class ScoutState(GotoState):

    def __init__(self):
        super().__init__(None)
        self.waiting = False

    def enter(self, context):
        self.waiting = True

    def get_random_path(self, context):
        self._progress = 0
        while True:
            self._target = context.world.get_random_cell(context.location, UNIT_SCOUT_RANGE)
            success, self._path = context.world.get_path(context.location, self._target, True)
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
            g = context.world.graph
            for cell in context.world.reveal(context.location):
                if g.is_in_bounds(cell) and g.get_terrain(cell)[0] is TerrainTypes.Tree:
                    print("Found a tree!")
                    unit = context.world.get_agents_in_state(WorkerState, 1)
                    if unit is not None:
                        found_tree_msg = Telegram(context.agent_id, unit.agent_id, MessageTypes.MSG_RESOURCE_FOUND, (TerrainTypes.Tree, cell))
                        context.world.dispatch(found_tree_msg)


