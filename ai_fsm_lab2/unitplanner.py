from state import StateContext, State

class UnitPlanner(StateContext):

    def __init__(self, world):
        super().__init__(UnitPlannerInit(), UnitPlannerGlobal())
        self._world = world

class UnitPlannerGlobal(State):
    pass

class UnitPlannerInit(State):
    pass
