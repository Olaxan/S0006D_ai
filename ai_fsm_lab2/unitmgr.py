from state import StateContext, State

class UnitManager(StateContext):

    def __init__(self, world):
        super().__init__(UnitManagerInit(), UnitManagerGlobal())
        self._world = world

class UnitManagerGlobal(State):
    pass

class UnitManagerInit(State):
    pass
