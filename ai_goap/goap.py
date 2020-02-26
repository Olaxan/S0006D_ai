from __future__ import annotations
from abc import ABC, abstractmethod

from ai_path.path import WeightedGraph, Path

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

    def plan(self, goal: WorldState):

        usable = set()

        for action in self._actions:
            action.do_reset()
            if action.checkProcedural():
                usable.add(action)

        tree = self.graph(usable, goal)
        Path.a_star_search(tree, None, None)

    def graph(self, actions, goal) -> bool:

        for action in actions:
            pass

        return False

    def clear(self):
        pass

