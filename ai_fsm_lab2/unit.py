from __future__ import annotations

from enum import Enum, auto
from random import randint

from config import *
from state import State, StateContext
from telegram import MessageTypes, Telegram
from world import BuildingTypes, ResourceTypes, TerrainTypes, World


class UnitTypes(Enum):
    Worker  = auto()
    Scout   = auto()

class PathStates(Enum):
    Idle        = auto()
    Waiting     = auto()
    Working     = auto()
    Error       = auto()
    Finished    = auto()

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

    def __init__(self, target, nodes=None, on_arrive=None, on_fail=None):
        self.on_arrive = on_arrive
        self.on_fail = on_fail
        self.target = target
        self.path = nodes
        self.progress = 0
        self.state = PathStates.Idle

    @property
    def length(self):
        return len(self.path)

    @property
    def valid(self):
        return len(self.path) > 0

    def has_arrived(self, context) -> bool:
        """Check if agent has arrived at target"""

        return self.target[0] == context.x and self.target[1] == context.y

    def on_finish(self, context):
        """Call once agent is finished with path, to change state appropriately"""

        self.state = PathStates.Idle
        if self.on_arrive is not None:
            context.change_state(self.on_arrive)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_PATH_DONE, context.location)
        context.world.dispatch(arrive_msg)

    def on_abort(self, context):
        """Call if agent failed pathing, to revert states appropriately"""

        self.state = PathStates.Idle
        if self.on_fail is not None:
            context.change_state(self.on_fail)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_PATH_FAIL, context.location)
        context.world.dispatch(arrive_msg)

    def enter(self, context):
        if self.path is None:
            context.world.path(context.location, self.target, on_finish=self.on_path, path_through_fog=False)
        else:
            self.target = self.path[-1]
            self.state = PathStates.Working

    def on_path(self, success, node_list):
        if success:
            self.path = node_list
            self.state = PathStates.Working
        else:
            self.state = PathStates.Error

    def execute(self, context, step):

        if self.state == PathStates.Working:
            for i in range(context.speed):
                cost = context.world.graph.cost(context.location)
                self.progress += step / cost
                if self.progress < self.length:
                    context.location = self.path[int(self.progress)]
                else:
                    context.location = self.target
                    self.on_finish(context)

        elif self.state == PathStates.Error:
            self.on_abort(context)

class PathErrorState(State):

    def enter(self, context):
        print("Agent is placed in a path error state!")

class ManagerState(State):

    def __init__(self):
        self.trees = []

    def enter(self, context):
        # make camp where manager stands
        context.world.add_location(BuildingTypes.Camp, context.location)

        # create initial scouts
        worker_pool = context.world.get_agents_in_state(WorkerState, INIT_SCOUT)

        for i in range(min(INIT_SCOUT, len(worker_pool) - 1)):
            scout_state = ScoutBehindState() if i == 0 else ScoutState()
            worker_pool[i].change_state(TrainingState(None, TIME_TRAIN_SCOUT, scout_state))

        builder_state = BuilderState()
        worker_pool[i + 1].change_state(TrainingState(None, TIME_TRAIN_BUILDER, builder_state))

        kiln_msg = Telegram(context.agent_id, worker_pool[i + 1].agent_id, MessageTypes.MSG_BUILDING_NEEDED, BuildingTypes.Kiln)
        context.world.dispatch(kiln_msg, TIME_TRAIN_BUILDER + 1)

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
            goto = GotoState(target[0], on_arrive=self)
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
                print("Need some mats!")
                data = (ResourceTypes.Log, context.location, BUILD_KILN_LOGS)
                resource_msg = Telegram(context.agent_id, None, MessageTypes.MSG_RESOURCE_NEEDED, data)
                context.world.dispatch(resource_msg)

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_BUILDING_NEEDED:
            print("Sure thing, boss!")
            camp_location = context.world.get_locations(BuildingTypes.Camp)
            build_origin = camp_location[0] if camp_location is not None else context.location
            build_site = context.world.get_random_cell(build_origin, 2)
            context.world.reveal(build_site)
            goto = GotoState(build_site, on_arrive=self)
            context.change_state(goto)
            self.is_building = True
            return

class WorkerState(State):

    def on_message(self, context, telegram):
        if telegram.message is MessageTypes.MSG_RESOURCE_FOUND:
            res, cell = telegram.data
            if res is TerrainTypes.Tree:
                print("Going to chop that tree down real good, eh!")
                state = WorkerLoggerState(cell)
                context.change_state(state)
                return True

        if telegram.message is MessageTypes.MSG_RESOURCE_NEEDED:
            res, cell, count = telegram.data
            context.change_state(WorkerFetchState(res, cell, count))
            return True

class WorkerLoggerState(WorkerState):

    def __init__(self, cell):
        self._target = cell
        self._timer = TIME_CHOP_TREE

    def enter(self, context):
        if context.location != self._target:
            context.change_state(GotoState(self._target, on_arrive=self))
            return

        print("Time to get a-choppin'!")

    def execute(self, context, step):
        self._timer -= step
        if self._timer <= 0:
            print("TIMBER!")
            context.world.graph.set_terrain(self._target, TerrainTypes.Stump)
            context.world.add_resource(context.location, ResourceTypes.Log)
            camp = context.world.get_locations(BuildingTypes.Camp)
            if camp is not None:
                print("Guess I'll carry this to the camp.")
                state = WorkerTransportState(context.location, camp[0], ResourceTypes.Log)
                context.change_state(state)
            else:
                print("I'll just leave this here, I suppose")
                context.change_state(WorkerState())

    def on_message(self, context, telegram):
        return False

class WorkerTransportState(WorkerState):

    def __init__(self, from_tile, to_tile, resource=None, count=1, search=False):
        self.resource = resource
        self.from_tile = from_tile
        self.to_tile = to_tile
        self.count = count
        self.search = search
        self.is_carrying = False

    def enter(self, context):
        if self.is_carrying and context.location == self.to_tile:
            count = context.world.add_resource(context.location, self.resource)
            print("Phew!")
            if count < self.count:
                goto = GotoState(self.from_tile, on_arrive=self)
                context.change_state(goto)
            else:
                context.change_state(WorkerState())
        elif context.location == self.from_tile:
            if context.world.get_resource(context.location, self.resource) > 0:
                self.is_carrying = True
                goto = GotoState(self.to_tile, on_arrive=self)
                context.change_state(goto)
            else:
                state = WorkerFetchState(self.resource, self.to_tile, self.count) if self.search else WorkerState()
                context.change_state(state)
        else:
            goto = GotoState(self.from_tile, on_arrive=self)
            context.change_state(goto)

    def on_message(self, context, telegram):
        return False

class WorkerFetchState(WorkerState):

    def __init__(self, resource, location, count):
        self.resource = resource
        self.location = location
        self.count = count

    def enter(self, context):
        context.world.path_nearest_resource(context.location, self.resource, lambda a, b: self.on_path(context, a, b))

    def on_path(self, context, success, nodes):
        if success:
            transport = WorkerTransportState(nodes[-1], self.location, self.resource, self.count)
            goto = GotoState(None, nodes=nodes, on_arrive=transport)
            context.change_state(goto)
        else:
            context.change_state(WorkerState())
            print("Can't find any of those...")

class ScoutState(GotoState):

    expeditions = 1

    def __init__(self):
        super().__init__(None)
        self.fail_timer = 60
        self.home = None

    def enter(self, context):
        context.speed = UNIT_SPEED_SCOUT
        self.state = PathStates.Idle
        self.home = context.world.get_locations(BuildingTypes.Camp)
        self.home = self.home[0] if self.home is not None else context.location

    def get_random_path(self, context):
        self.target = context.world.get_random_cell(self.home, UNIT_SCOUT_RANGE + ScoutState.expeditions)
        context.world.path(context.location, self.target, on_finish=self.on_path, path_through_fog=True)

    def on_finish(self, context):
        self.state = PathStates.Idle
        ScoutState.expeditions += 1

    def on_abort(self, context):
        self.state = PathStates.Idle

    def on_path(self, success, node_list):
        if success:
            self.progress = 0
            self.path = node_list
            self.state = PathStates.Working
        else:
            self.state = PathStates.Waiting

    def execute(self, context, step):
        if self.state == PathStates.Idle:
            self.state = PathStates.Waiting
            self.get_random_path(context)
        elif self.state == PathStates.Working:
            super().execute(context, step)
            g = context.world.graph
            for cell in context.world.reveal(context.location):
                if g.is_in_bounds(cell) and g.get_terrain(cell)[0] is TerrainTypes.Tree:
                    unit = context.world.get_agents_in_state(WorkerState, 1)
                    if unit is not None:
                        found_tree_msg = Telegram(context.agent_id, unit.agent_id, MessageTypes.MSG_RESOURCE_FOUND, (TerrainTypes.Tree, cell))
                        context.world.dispatch(found_tree_msg)

class ScoutBehindState(ScoutState):

    def __init__(self):
        super().__init__()
        self.fail_timer = 30

    def get_random_path(self, context):
        context.world.path_nearest_fog(context.location, on_finish=self.on_path)

    def on_path(self, success, node_list):
        super().on_path(success, node_list)
        if success:
            self.target = node_list[-1]
        else:
            self.state = PathStates.Error
