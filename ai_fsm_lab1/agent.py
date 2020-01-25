from state import State, StateContext, Goto
from world import World
from random import randint
from utils import Clamped

class Agent(StateContext):

    _location = [0, 0]
    _name = "Agent"
    _world = None
    _id = 0

    home:   str = None
    work:   str = None

    def __init__(self, world: World, name: str, home: str, work: str):
        super().__init__(SleepState(), None, name)
        self._world = world
        self._id = self._world.register_agent(self)

        self.home = home
        self.work = work
        
        self.money  = 0
        self.sleep  = Clamped(0, 10, 5)
        self.hunger = Clamped(0, 5, 0)
        self.thirst = Clamped(0, 5, 0)
        self.social = Clamped(0, 10, 5)

    def __del__(self):
        self.describe("dead")

    def start(self):
        super().start()
        self.location = self.world.get_location(self.home)

    def is_at(self, location: str) -> bool:
        return self._world.is_at(self, location)

    def goto(self, location: str, on_arrive: State = None):
        current = self._current_state
        target = self.world.get_location(location)
        self.describe("going to %s for %s" % (location.capitalize(), current.state_name))
        self.change_state(Goto(target, on_arrive), False)

    def describe(self, action):
        print(self.name, "is", action)

    def say(self, phrase):
        print("%s: '%s'" % (self.name, phrase))

    @property
    def id(self):
        return self._id

    @property
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

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location: [int, int]):
        self._location = location

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
            self.context.change_state(SleepState())

        if self.context.thirst.is_max:
            self.context.change_state(DrinkState())

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
            self.context.change_state(EatState())

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
            self.context.change_state(WorkState())

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
        #self.context.drunk.add(3)
        
        if self.context.thirst.is_min:
            self.context.change_state(WorkState())
