from __future__ import annotations
from abc import ABC, abstractmethod

class WorldState():

    _state: dict = {}

    def __init__(self, state: dict):
        _state = state

    def add_state(self, key: str, state: bool):
        self._state[key] = state

    def remove_state(self, key: str):
        self._state.pop(key)

class Action():

    _preconditions = {}
    _effects = {}

    _key = "Action"
    _cost = 1

    def __init__(self, key: str, cost: int, pre: list, post: list):
        self._key = key
        self._cost = cost

    def add_precondition(self, state: WorldState) -> None:
        self._preconditions[state._property_key] = state

    def remove_precondition(self, key: str) -> None:
        self._preconditions.pop(key)

    def add_effect(self, state: WorldState) -> None:
        self._effects[state._property_key] = state

    def remove_effect(self, key: str) -> None:
        self._effects.pop(key)

    @property
    def preconditions(self) -> dict:
        return self._preconditions

    @preconditions.setter
    def preconditions(self, preconditions: dict) -> None:
        self._preconditions = preconditions

    @property
    def effects(self) -> dict:
        return self._preconditions

    @effects.setter
    def effects(self, effects: dict) -> None:
        self._effects = effects

    @abstractmethod
    def checkProcedural(self) -> bool:
        pass

    @abstractmethod
    def execute_action(self) -> bool:
        pass

class Node():

    parent: Node
    cost: int
    state: WorldState
    action: Action

    def __init__(self, parent: Node, cost: int, state: WorldState, action: Action):
        self.parent = parent
        self.cost = cost
        self.state = state
        self.action = action

class Planner():

    _actions = []
    _world = None

    def __init__(self, actions: list, state: WorldState):
        self._actions = actions
        self._world = state

    def plan(self, goal: WorldState) -> list:

        for a in self._actions:
            a.do_reset()

        usable: set
        for a in self._actions:
            if a.checkProcedural(): usable.add(a)

        leaves: list
        result = list
        cheapest = None
        start = Node(None, 0, self._world, None)
        success = self.graph(start, leaves, self._actions, goal)

        if not success: return None

        for leaf in leaves:
            if cheapest == None or leaf.cost < cheapest.cost:
                cheapest = leaf

        n = cheapest
        while n != None:
            if n.action != None: result.insert(0, n.action)
            n = n.parent

        return result

    def graph(self, start: Node, leaves: list, actions: set, goal: set) -> bool:
        
        found = False

        for action in actions:
            pass

        return False

    def clear(self):
        pass

