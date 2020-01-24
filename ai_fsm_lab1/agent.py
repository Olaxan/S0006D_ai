from state import State, StateContext
from random import randint
from utils import Clamped

class Agent(StateContext):

    home:   str = None
    work:   str = None

    def __init__(self, name: str, home: str, work: str):
        super().__init__(SleepState(), name)
        self.home = home
        self.work = work
        self.money  = 0
        self.drunk  = Clamped(0, 10)
        self.sleep  = Clamped(0, 10, 5)
        self.hunger = Clamped(0, 5, 0)
        self.thirst = Clamped(0, 5, 0)
        self.social = Clamped(0, 10, 5)

    def __del__(self):
        print(self.name, "is dead")

    def update(self):
        super().update()
        self.drunk.sub(1)

    def start(self):
        super().start()
        self.location = self.world.get_location(self.home)

    def say(self, phrase):
        if self.drunk.is_min:
            super().say(phrase)
        else: 
            print("%s: '*hic!* %s'" % (self.name, phrase))

class AgentState(State):

    @property
    def context(self) -> Agent:
        return self._context

    @context.setter
    def context(self, context: Agent):
        self._context = context

class IdleState(AgentState):

    def execute(self):
        if randint(0, 100) == 1: self.context.describe("milling around")

class WorkState(AgentState):

    state_name = "work"

    def enter(self):
        if self.context.is_at(self.context.work):
            self.context.say("Dreading work today...")
        else:
            self.context.goto(self.context.work)

    def exit(self):
        self.context.say("No more of this!")

    def execute(self):

        self.context.money += 125
        self.context.thirst.add(2)
        self.context.sleep.add(2)

        self.context.say("Ka-ching! Got %d:- now!" % self.context.money)

        if self.context.sleep.is_max:
            self.context.changeState(SleepState())

        if self.context.thirst.is_max:
            self.context.changeState(DrinkState())

class SleepState(AgentState):

    state_name = "some sleep"

    def enter(self):
        if self.context.is_at(self.context.home):
            self.context.say("Time for a nap - I'm an agent who loves to snooze")
        else:
            self.context.goto(self.context.home)

    def exit(self):
        self.context.describe("waking up")

    def execute(self):

        if randint(0, self.context.sleep.max) == 1: self.context.say("zZzzzZzz...")

        self.context.sleep.sub(2)
        self.context.hunger.add(2)
        
        if self.context.sleep.is_min:
            self.context.changeState(EatState())

class EatState(AgentState):

    state_name = "a bite"

    def enter(self):
        if self.context.is_at("dallas"):
            self.context.say("I am hungry, I want some lasagna")
        else:
            self.context.goto("dallas")

    def exit(self):
        self.context.describe("full!")

    def execute(self):

        if randint(0, self.context.hunger.max) == 1: self.context.say("Crunch!")
        
        self.context.hunger.sub(2)
        
        if self.context.hunger.is_min:
            self.context.changeState(WorkState())

class DrinkState(AgentState):

    state_name = "a drink"

    def enter(self):
        if self.context.is_at("travven"):
            self.context.describe("crackin' open a cold'un")
            self.context.money -= 30
        else:
            self.context.goto("travven")

    def exit(self):
        self.context.describe("finishing his drink")

    def execute(self):

        if randint(0, self.context.thirst.max) == 1: self.context.say("Slurp!")
        
        self.context.thirst.sub(2)
        self.context.drunk.add(3)
        
        if self.context.thirst.is_min:
            self.context.changeState(WorkState())
