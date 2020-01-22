from __future__ import annotations
from abc import ABC, abstractmethod

class Action(ABC):

    _preconditions = {}
    _effects = {}

    _is_in_range = False
    _cost = 1

    _target = None

    def add_precondition(self, key: str, condition: bool) -> None:
        self._preconditions[key] = condition

    def remove_precondition(self, key: str) -> None:
        self._preconditions.pop(key)

    def add_effect(self, key: str, effect: bool) -> None:
        self._effects[key] = effect

    def remove_effect(self, key: str) -> None:
        self._effects.pop(key)

    def do_reset(self):
        _is_in_range = False
        _target = None
        self.reset()

    def reset(self) -> None:
        pass

    @property
    def in_range(self) -> bool:
        return self._is_in_range

    @in_range.setter
    def in_range(self, is_in_range: bool) -> None:
        self._is_in_range = is_in_range

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
    def is_done(self) -> bool:
        pass

    @abstractmethod
    def requires_in_range(self) -> bool:
        pass

    @abstractmethod
    def checkProcedural(self, agent: int) -> bool:
        pass

    @abstractmethod
    def execute_action(self) -> bool:
        pass

class Node():

    parent: Node
    cost: int
    state: set
    action: Action

    def __init__(self, parent: Node, cost: int, state: set, action: Action):
        self.parent = parent
        self.cost = cost
        self.state = state
        self.action = action

class Planner():

    def plan(self, agent: int, actions: set, state: set, goal: set):

        for a in actions:
            a.do_reset()

        usable: set
        for a in actions:
            if a.checkProcedural(agent): usable.add(a)

        leaves: list
        result = list
        cheapest = None
        start = Node(None, 0, state, None)
        success = self.graph(start, leaves, actions, goal)

        if not success: return None

        for leaf in leaves:
            if cheapest == None or leaf.cost < cheapest.cost:
                cheapest = leaf

        n = cheapest
        while n != None:
            if n.action != None: result.insert(0, n.action)
            n = n.parent

        return result

    def check_state(self, test: dict, state: dict) -> bool:

        for t in test:
            match = False
            for s in state:
                if s == t:
                    match = True
                    break
            if not match:
                return False
        return True

    def graph(self, start: Node, leaves: list, actions: set, goal: set) -> bool:
        
        found = False

        for action in actions:
            pass