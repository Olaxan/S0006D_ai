from state import State, StateContext
from random import randint
from utils import Clamped

class Agent(StateContext):

    money       = Clamped(0)
    sleep       = Clamped(0, 0, 100)
    hunger      = Clamped(10, 0, 50)
    thirst      = Clamped(0, 0, 25)
    social      = Clamped(25, 0, 50)

    home = (0, 0)

    def __init__(self, id: int, name: str, home: (int, int)):
        super().__init__(IdleState(), id, name)
        self.name = name
        self.home = home

    def update(self):
        super().update()
        self.hunger.add()
        self.thirst.add()
        self.social.add()
        self.sleep.add()

class AgentState(State):

    @property
    def context(self) -> Agent:
        return self._context

    @context.setter
    def context(self, context: Agent):
        self._context = context

class GotoState(AgentState):

    _target = (0, 0)
    _on_arrive: AgentState = IdleState()

    def __init__(self, location: (int, int), on_arrive: AgentState):
        self._on_arrive = on_arrive
        self._target = location

    def _has_arrived(self) -> bool:
        return self._target[0] == self.context.x and self._target[1] == self.context.y

    def enter(self):
        if not self._has_arrived():
            self.describe("moving to a new location:", self._target)

    def update(self):

        if self._has_arrived():
            self.context.changeState(self._on_arrive)
            return

        if self._target[0] > self.context.x: self.context.x -= 1
        elif self._target[0] < self.context.x: self.context.y += 1

        if self._target[1] > self.context.y: self.context.y -= 1
        elif self._target[1] < self.context.y: self.context.y += 1

class IdleState(AgentState):

    def execute(self):
        if randint(0, 100) == 1: self.describe("milling around")

class SleepState(AgentState):

    def enter(self):
        self.describe("going to bed")

    def exit(self):
        self.describe("waking up")

    def execute(self):

        if randint(0, 100) == 5: self.describe("fast asleep")

        self.context.sleep.subtract(3)
        
        if self.context.sleep == 0:
            self.context.changeState(IdleState())

class EatState(AgentState):

    def enter(self):
        self.describe("cooking something")

    def exit(self):
        self.describe("full!")

    def execute(self):
        self.context.hunger.subtract(5)
        
        if self.context.hunger == 0:
            self.context.changeState(IdleState())

class DrinkState(AgentState):

    def enter(self):
        self.describe("crackin' open a cold'un")

    def exit(self):
        self.describe("finishing his drink")

    def execute(self):
        self.context.thirst.subtract(5)

        if self.context.thirst == 0:
            self.context.changeState(IdleState())
