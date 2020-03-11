from __future__ import annotations

from enum import Enum, auto
from math import ceil
from random import randint

from config import *
from state import State, StateContext
from telegram import MessageTypes, Telegram
from world import BuildingTypes, ResourceTypes, TerrainTypes, World

class PathStates(Enum):
    Idle        = auto()
    Waiting     = auto()
    Working     = auto()
    Searching   = auto()
    Error       = auto()
    Finished    = auto()

class Actions(Enum):
    Idle        = auto()
    Waiting     = auto()
    Working     = auto()
    Walking     = auto()

class Unit(StateContext):

    def __init__(self, world: World, location, state):
        super().__init__(state(), UnitGlobal())
        self._world = world
        self._location = list(location)
        self.speed = UNIT_SPEED
        self.color = COL_UNIT

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
            for i in range(ceil(context.speed * step)):
                cost = context.world.graph.cost(context.location)
                self.progress += 1 / cost
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
        context.world.add_location(context.location, BuildingTypes.Camp)

        # create initial scouts
        worker_pool = context.world.get_agents_in_state(WorkerState)

        for i in range(INIT_SCOUT):
            scout_state = ScoutBehindState() if i == 0 else ScoutState()
            worker_pool[i].change_state(TrainingState(None, TIME_TRAIN_SCOUT, scout_state))

        for j in range(INIT_LOGGER):
            worker_pool[i + j + 1].change_state(WorkerLoggerState())

        worker_pool[-1].change_state(TrainingState(None, TIME_TRAIN_BUILDER, BuilderState()))
        kiln_msg = Telegram(context.agent_id, worker_pool[-1].agent_id, MessageTypes.MSG_BUILDING_NEEDED, BuildingTypes.Kiln)
        context.world.dispatch(kiln_msg, TIME_TRAIN_BUILDER + 1)

    def on_message(self, context, telegram):

        if telegram.message == MessageTypes.MSG_BUILDING_NEEDED:
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
        elif telegram.message == MessageTypes.MSG_RESOURCE_NEEDED:
            res, cell, count = telegram.data
            print("I'll get someone right on it.")
            worker_pool = context.world.get_agents_in_state(WorkerState, 3)
            for w in worker_pool:
                w.change_state(WorkerFetchState(res, cell, count))
        elif telegram.message == MessageTypes.MSG_BUILDING_DONE:
            building, location = telegram.data
            if building == BuildingTypes.Kiln:
                worker = context.world.get_agents_in_state(WorkerState, 1)
                if worker is not None:
                    worker.change_state(TrainingState(BuildingTypes.Kiln, TIME_TRAIN_KILNER, Kilner(location)))

class TrainingState(State):

    def __init__(self, location_type, time, after_train):
        self.begun = False
        self.location_type = location_type
        self.after_train = after_train
        self.timer = time

    def check_building(self, context):
        target = context.world.get_locations(self.location_type)
        if target is None:
            print("Need a {} to train for this!".format(self.location_type))
            manager = context.world.get_agents_in_state(ManagerState, 1)
            build_msg = Telegram(context.agent_id, manager.agent_id, MessageTypes.MSG_BUILDING_NEEDED, self.location_type)
            context.world.dispatch(build_msg)
        else:
            if context.location == target[0]:
                self.begun = True
                print("Training at {} ({})".format(self.location_type.name, type(self.after_train)))
            else:
                goto = GotoState(target[0], on_arrive=self)
                context.change_state(goto, False)

    def enter(self, context):
        context.color = COL_TRAINING
        if self.location_type is None:
            self.begun = True
            print("Training! ({})".format(type(self.after_train)))
        else:
            self.check_building(context)

    def execute(self, context, step):
        if self.begun:
            self.timer -= step
            if self.timer <= 0:
                context.change_state(self.after_train)

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_BUILDING_DONE and telegram.data[0] is self.location_type:
            self.check_building(context)
            return True

class BuilderState(State):

    def __init__(self):
        self.building = None
        self.has_begun = False

    @property
    def resource(self):
        return self.building.value[0]

    @property
    def count(self):
        return self.building.value[1]

    @property
    def time(self):
        return self.building.value[2]

    def check_requirements(self, context):
        if self.building is not None and not self.has_begun:
            res = context.world.get_resource(context.location, self.resource)
            if res < self.count:
                print("Need some mats!")
                data = (self.resource, context.location, self.count)
                mgr = context.world.get_agents_in_state(ManagerState, 1)
                if mgr is not None:
                    resource_msg = Telegram(context.agent_id, mgr.agent_id, MessageTypes.MSG_RESOURCE_NEEDED, data)
                    context.world.dispatch(resource_msg)
            else:
                print("Beginning construction!")
                context.world.add_resource(context.location, self.resource, -self.count)
                check_msg = Telegram(context.agent_id, context.agent_id, MessageTypes.MSG_BUILDING_FINISH)
                context.world.dispatch(check_msg, self.time)
                self.has_begun = True

    def enter(self, context):
        context.color = COL_BUILDER
        self.check_requirements(context)

    def on_message(self, context, telegram):

        if telegram.message == MessageTypes.MSG_BUILDING_NEEDED:
            print("Sure thing, boss!")
            camp_location = context.world.get_locations(BuildingTypes.Camp)
            build_origin = camp_location[0] if camp_location is not None else context.location
            build_site = context.world.get_random_cell(build_origin, 2)
            context.world.reveal(build_site)
            goto = GotoState(build_site, on_arrive=self)
            context.change_state(goto)
            self.building = telegram.data
            return True
        elif telegram.message == MessageTypes.MSG_RESOURCE_CHANGE and self.building is not None and not self.has_begun:
            if telegram.data[:2] == (self.resource, context.location) and telegram.data[2] >= self.count:
                print("Cheers, lads!")
                self.check_requirements(context)
                return True
        elif telegram.message == MessageTypes.MSG_BUILDING_FINISH:
            print("Job's done!")
            context.world.add_location(context.location, self.building)
            done_msg = Telegram(context.agent_id, None, MessageTypes.MSG_BUILDING_DONE, data=(self.building, context.location))
            context.world.dispatch(done_msg)
            self.building = None
            self.has_begun = False
            t = context.world.get_random_cell(context.location, 2)
            context.change_state(GotoState(t, on_arrive=self))
            return True

class WorkerState(State):

    def enter(self, context):
        context.color = COL_UNIT

    def on_message(self, context, telegram):

        if telegram.message is MessageTypes.MSG_RESOURCE_NEEDED:
            res, cell, count = telegram.data
            context.change_state(WorkerFetchState(res, cell, count))
            return True

class WorkerLoggerState(WorkerState):

    def __init__(self):
        self.state = Actions.Idle
        self.timer = 0

    def enter(self, context):
        context.color = COL_LOGGER
        if self.state == Actions.Walking:
            self.state = Actions.Working
            self.timer = TIME_CHOP_TREE

    def on_path(self, context, success, nodes):
        if success:
            self.state = Actions.Walking
            goto = GotoState(nodes[-1], on_arrive=self)
            context.change_state(goto)
        else:
            self.state = Actions.Idle

    def execute(self, context, step):
        if self.state == Actions.Working:
            self.timer -= step
            if self.timer <= 0:
                context.world.graph.set_tile(context.location, TerrainTypes.Stump, 1)
                context.world.add_resource(context.location, ResourceTypes.Log)
                self.state = Actions.Idle
                self.timer = TIME_CHOP_TREE
        elif self.state == Actions.Idle:
            self.state = Actions.Waiting
            context.world.path_nearest_terrain(context.location, TerrainTypes.Tree, lambda a, b: self.on_path(context, a, b))

    def on_message(self, context, telegram):
        return False

class WorkerTransportState(WorkerState):

    def __init__(self, from_tile, to_tile, resource=None, count=1, on_finish=None):
        self.resource = resource
        self.from_tile = from_tile
        self.to_tile = to_tile
        self.count = count
        self.is_carrying = False
        self.on_finish = on_finish

    def enter(self, context):
        if self.is_carrying and context.location == self.to_tile:
            # Place carried item
            self.is_carrying = False
            count = context.world.add_resource(context.location, self.resource)

            msg_res = Telegram(context.agent_id, None, MessageTypes.MSG_RESOURCE_CHANGE, data=(self.resource, self.to_tile, count))
            context.world.dispatch(msg_res)

            if count < self.count:
                goto = GotoState(self.from_tile, on_arrive=self)
                context.change_state(goto)
            else:
                state = self.on_finish if self.on_finish is not None else WorkerState()
                context.change_state(state)
        elif context.location == self.from_tile:
            # Grab item to carry
            if context.world.get_resource(context.location, self.resource) > 0:
                context.world.add_resource(context.location, self.resource, -1)
                self.is_carrying = True
                goto = GotoState(self.to_tile, on_arrive=self)
                context.change_state(goto)
            else:
                state = self.on_finish if self.on_finish is not None else WorkerState()
                context.change_state(state)
        else:
            # Goto pickup site for items
            goto = GotoState(self.from_tile, on_arrive=self)
            context.change_state(goto)

class WorkerFetchState(WorkerState):

    def __init__(self, resource, location, count):
        self.resource = resource
        self.location = location
        self.count = count
        self.state = Actions.Idle
        self.fail_timer = randint(0, 5)

    def enter(self, context):
        context.color = COL_FETCHER
        if self.state == Actions.Working:
            self.state = Actions.Idle

    def on_path(self, context, success, nodes):
        if success:
            self.state = Actions.Working
            trans = WorkerTransportState(nodes[-1], self.location, self.resource, self.count, on_finish=self)
            context.change_state(trans)
        else:
            self.state = Actions.Idle
            self.fail_timer = 1 + randint(0, 5)

    def execute(self, context, step):
        self.fail_timer -= step
        if self.state == Actions.Idle and self.fail_timer <= 0:
            self.state = Actions.Waiting
            finish = lambda a, b: self.on_path(context, a, b)
            context.world.path_nearest_resource(context.location, self.resource, on_finish=finish, exclude=[self.location])

    def on_message(self, context, telegram):

        if telegram.message == MessageTypes.MSG_RESOURCE_CHANGE:
            if telegram.data[:2] == (self.resource, self.location) and telegram.data[2] >= self.count:
                context.change_state(WorkerState())
                return True

class ScoutState(GotoState):

    expeditions = 1

    def __init__(self):
        super().__init__(None)
        self.fail_timer = randint(0, 5)
        self.home = None

    def enter(self, context):
        context.speed = UNIT_SPEED_SCOUT
        context.color = COL_SCOUT
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
            self.state = PathStates.Idle
            self.fail_timer = 60 + randint(0, 120)

    def execute(self, context, step):
        self.fail_timer -= step
        if self.state == PathStates.Idle and self.fail_timer <= 0:
            self.state = PathStates.Waiting
            self.get_random_path(context)
        elif self.state == PathStates.Working:
            super().execute(context, step)
            g = context.world.graph
            for cell in context.world.reveal(context.location):
                if g.is_in_bounds(cell) and g.get_terrain(cell) is TerrainTypes.Tree:
                    mgr = context.world.get_agents_in_state(ManagerState, 1)
                    if mgr is not None:
                        found_tree_msg = Telegram(context.agent_id, mgr.agent_id, MessageTypes.MSG_RESOURCE_FOUND, (TerrainTypes.Tree, cell))
                        context.world.dispatch(found_tree_msg)

class ScoutBehindState(ScoutState):

    def __init__(self):
        super().__init__()
        self.fail_timer = randint(0, 5)

    def get_random_path(self, context):
        camp = context.world.get_locations(BuildingTypes.Camp)[0]
        context.world.path_nearest_fog(camp, on_finish=self.on_path)

    def on_path(self, success, node_list):
        self.path = node_list
        if self.state == PathStates.Waiting:
            if len(node_list) > MAX_DIJKSTRA_SCOUT_DIST:
                self.state = PathStates.Error
                print("Behind scout reverting to regular scout mode")
            else:
                self.state = PathStates.Searching if success else PathStates.Error
        elif self.state == PathStates.Searching:
            if success:
                self.progress = 0
                self.target = node_list[-1]
                self.state = PathStates.Working
            else:
                self.fail_timer = 1 + randint(0, 5)
                self.state = PathStates.Idle


    def execute(self, context, step):
        super().execute(context, step)
        if self.state == PathStates.Error:
            context.change_state(ScoutState())
        elif self.state == PathStates.Searching:
            context.world.path(context.location, self.path[-1], on_finish=self.on_path, path_through_fog=True)

class Kilner(State):

    def __init__(self, kiln_site):
        self.location = kiln_site
        self.state = Actions.Idle
        self.timer = 0

    def enter(self, context):
        context.color = COL_KILNER
        if context.location == self.location:
            self.state = Actions.Idle
        else:
            context.change_state(GotoState(self.location, on_arrive=self))

    def execute(self, context, step):
        if self.state == Actions.Idle:
            if context.world.get_resource(context.location, ResourceTypes.Log) >= PRODUCE_COAL_LOGS:
                context.world.add_resource(context.location, ResourceTypes.Log, -PRODUCE_COAL_LOGS)
                self.timer = TIME_PRODUCE_COAL
                self.state = Actions.Working
            else:
                self.state = Actions.Waiting
                resource_data = (ResourceTypes.Log, self.location, 10)
                mgr = context.world.get_agents_in_state(ManagerState, 1)
                if mgr is not None:
                    print("Need logs to make coal!")
                    res_msg = Telegram(context.agent_id, mgr.agent_id, MessageTypes.MSG_RESOURCE_NEEDED, data=resource_data)
                    context.world.dispatch(res_msg)
        elif self.state == Actions.Working:
            self.timer -= step
            if self.timer <= 0:
                c = context.world.add_resource(context.location, ResourceTypes.Coal)
                l = context.world.get_resource(context.location, ResourceTypes.Log)
                print("Coal: {} / Logs: {}".format(c, l))
                self.state = Actions.Waiting

    def on_message(self, context, telegram):

        if telegram.message == MessageTypes.MSG_RESOURCE_CHANGE and self.state == Actions.Waiting:
            res, cell, count = telegram.data
            if (res, cell) == (ResourceTypes.Log, self.location) and count > 0:
                self.state = Actions.Idle
