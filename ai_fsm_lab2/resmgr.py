from state import StateContext, State

class ResourceManager(StateContext):

    def __init__(self, world):
        super().__init__(ResourceManagerInit(), ResourceManagerGlobal())
        self._world = world

class ResourceManagerGlobal(State):
    pass

class ResourceManagerInit(State):
    pass
