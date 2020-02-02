import copy

from state import State, StateContext
from random import randint
from world import World
from telegram import Telegram, MessageTypes
from utils import Clamped

class Agent(StateContext):

    _location = [0, 0]
    _name = "Agent"
    _world = None
    _id = 0

    home:   str = None
    work:   str = None

    speed   = None
    money   = None
    drunk   = None
    sleep   = None
    hunger  = None
    social  = None
    thirst  = None
    bladder = None

    def __init__(self, world: World, name: str, home: str, work: str):
        super().__init__(SleepState(), GlobalState())
        self._name = name
        self._world = world
        self._location = [0, 0]
        self._id = self._world.register_agent(self)

        self.home = home
        self.work = work

        self.speed = 5
        
        self.money   = 0
        self.drunk   = Clamped(0, 0)
        self.sleep   = Clamped(7, 0, 8)
        self.bladder = Clamped(5, 0, 10)
        self.hunger  = Clamped(0, 0, 5)
        self.thirst  = Clamped(0, 0, 5)
        self.social  = Clamped(5, 0, 10)

    def __del__(self):
        self.describe("dead")

    def init(self):
        super().start()
        self.location = copy.copy(self.world.get_location(self.home))

    def is_at(self, location: str) -> bool:
        return self._world.is_at(self, location)

    def goto(self, location: str, on_arrive: State = None):

        if on_arrive is None: on_arrive = self._current_state

        target = self.world.get_location(location)
        eta = GotoState.estimate(self.location, target, self.speed)

        self.describe("going to {} for {} (ETA: {})".format(location.capitalize(), on_arrive.state_name, World.time_format_24(self.world.time + eta)))
        self.change_state(GotoState(target, self.speed, on_arrive), False)

    def describe(self, action):
        print("[{}] {} is {}".format(self.world.time_24, self.name, action))

    def say(self, phrase):
        if self.drunk.is_min:
            print("[{}] {}: '{}'".format(self.world.time_24, self.name, phrase))
        else:
            print("[{}] {}: '*hic!* {}'".format(self.world.time_24, self.name, phrase))

    def say_to(self, other, phrase):
        if self.drunk.is_min:
            print("[{}] {}, to {}: '{}'".format(self.world.time_24, self.name, other.name, phrase))
        else:
            print("[{}] {}, to {}: '*hic!* {}'".format(self.world.time_24, self.name, other.name, phrase))


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

class GotoState(AgentState):

    _target = [0, 0]
    _on_arrive: None
    _speed = 1

    state_name = "a walk"
    state_verb = "walking"

    @staticmethod
    def estimate(location, target, speed):
        delta_x = abs(location[0] - target[0])
        delta_y = abs(location[1] - target[1])
        return max(delta_x / speed, delta_y / speed)

    def __init__(self, location: [int, int], speed = 1, on_arrive: State = None):
        self._on_arrive = on_arrive
        self._target = location
        self._speed = speed

    def _has_arrived(self) -> bool:
        return self._target[0] == self.context.x and self._target[1] == self.context.y

    def exit(self):
        msg = Telegram(self.context.id, None, MessageTypes.MSG_ARRIVAL, self.context.location)
        self.context.world.dispatch(0, msg)

    def execute(self, step):

        if self._has_arrived():
            self.context.change_state(self._on_arrive) if self._on_arrive is not None else self.context.revert_state()
            return

        delta_x = self._target[0] - self.context.x
        if delta_x != 0:
            sign_x = delta_x / abs(delta_x)
            self.context.x += max(delta_x, sign_x * self._speed * step) if sign_x < 0 else min(delta_x, sign_x * self._speed * step)

        delta_y = self._target[1] - self.context.y
        if delta_y != 0:
            sign_y = delta_y / abs(delta_y)
            self.context.y += max(delta_y, sign_y * self._speed * step) if sign_y < 0 else min(delta_y, sign_y * self._speed * step)

class GlobalState(AgentState):

    def execute(self, step):
        self.context.drunk.sub(1 * step)
        self.context.social.add((randint(0, 5) == 1) * step)
        self.context.bladder.add((randint(0, 5) == 1) * step)

        if self.context.state.ignore_global:
            return

        if self.context.bladder.is_max:
            self.context.change_state(ToiletState())
            return

    def on_message(self, telegram: Telegram):

        if telegram.message == MessageTypes.MSG_MEETING:
            eta = GotoState.estimate(self.context.location, self.context.world.get_location(telegram.data), self.context.speed)
            sender = self.context.world.get_agent(telegram.sender_id)

            if self.context.location == sender.location:
                self.context.say_to(sender, "I'm at {}, too! Hang on, let me come over".format(telegram.data.capitalize()))
            else:
                self.context.say_to(sender, "You know it! I'm {} right now, but I'll be over in like {} minutes!".format(self.context.state.state_verb, int(60 * eta)))
                
            reply = Telegram(self.context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, True)
            self.context.world.dispatch(0, reply)
            self.context.change_state(MeetingState(telegram.data))

        if telegram.message == MessageTypes.MSG_MEETING_REPLY:
            if telegram.data == True:
                self.context.say("Sick. I'll be waiting for you!")
                self.context.change_state(MeetingState(None), False)
            else:
                self.context.say("No worries. See you some other time!")

        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == self.context.location:
            agent = self.context.world.get_agent(telegram.sender_id)
            self.context.say("Hey {}!".format(agent.name))

class WorkState(AgentState):

    state_name = "work"
    state_verb = "working"
    start_hour = 8.5
    end_hour = 17

    def enter(self):
        if self.context.is_at(self.context.work):
            if self.context.world.hour_24 <= self.start_hour:
                if self.context.world.time > self.start_hour:
                    self.context.say("Oh, running a bit late...")
                else:
                    self.context.say("Back in the hamster wheel")
            else:
                self.context.say("Well, back at it")
        else:
            self.context.goto(self.context.work)

    def exit(self):
        if self.context.world.hour_24 >= self.end_hour:
            self.context.say("Finally!")
        else:
            self.context.say("Just {0} hours left...".format(self.end_hour - self.context.world.hour_24))

    def execute(self, step):

        self.context.money += 125 * step
        self.context.thirst.add(2 * step)
        self.context.sleep.add(2 * step)
        self.context.hunger.add(1 * step)

        if randint(0, int(self.end_hour - self.start_hour)) == 1:
            self.context.say("Ka-ching! Got {}:- now!".format(self.context.money))

        if self.context.world.hour_24 >= self.end_hour:
            self.context.change_state(EatState())
            return

        if self.context.sleep.is_max:
            self.context.change_state(WorkSleepState())
            return

        if self.context.thirst.is_max:
            self.context.change_state(WorkDrinkState())
            return

        if self.context.hunger.is_max:
            self.context.change_state(WorkEatState())
            return

    def on_message(self, telegram: Telegram):
        if telegram.message == MessageTypes.MSG_MEETING:
            self.context.say("Ah, naw mate, sorry, can't meet right now, I'm at work!")
            reply = Telegram(self.context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
            self.context.world.dispatch(0, reply)
            return True
        return False

class WorkEatState(AgentState):

    state_name = "a sandwich"
    state_verb = "eating a sandwich"
    ignore_global = True
    sandwich_units = 5

    def enter(self):
        self.context.describe("getting out his lunch from his bag")

    def exit(self):
        self.context.describe("returning to work")

    def execute(self, step):
        
        if randint(0, self.context.hunger.max) == 1: self.context.say("Krunch!")

        self.context.hunger.sub(self.sandwich_units)
        self.context.revert_state()

class WorkDrinkState(AgentState):

    state_name = "a sip of water"
    state_verb = "having a water break"
    ignore_global = True

    def enter(self):
        self.context.describe("going to the loo for a sip of water")

    def exit(self):
        self.context.describe("returning to work")

    def execute(self, step):
        
        if randint(0, self.context.thirst.max) == 1: self.context.say("Slurp!")

        self.context.thirst.sub(10)
        self.context.bladder.add(1)

        if self.context.thirst.is_min:
            self.context.revert_state()

class WorkSleepState(AgentState):

    state_name = "a cup of coffee"
    state_verb = "having a cuppa"
    ignore_global = True
    coffee_units = 3

    def enter(self):
        self.context.describe("going to the breakroom for some coffee")

    def exit(self):
        self.context.describe("returning to work")

    def execute(self, step):
        
        if randint(0, self.context.sleep.max) == 1: self.context.say("Sörpl!")

        self.context.sleep.sub(self.coffee_units)
        self.context.bladder.add(1)

        self.context.revert_state()

class SleepState(AgentState):

    state_name = "some sleep"
    state_verb = "sleeping"

    def enter(self):
        if self.context.is_at(self.context.home):
            wakeup_time = WorkState.start_hour - GotoState.estimate(self.context.location, self.context.world.get_location(self.context.work), self.context.speed) - 0.25
            self.context.say("Time for a nap - I'm an agent who loves to snooze")
            self.context.say("Lessee, I have to wake up at around... {0}!".format(World.time_format_24(wakeup_time)))
            alarm = Telegram(self.context.id, self.context.id, MessageTypes.MSG_WAKEUP)
            self.context.world.dispatch_scheduled(wakeup_time, alarm)
        else:
            self.context.goto(self.context.home)

    def exit(self):
        self.context.describe("waking up")

    def execute(self, step):

        if randint(0, self.context.sleep.max) == 1: self.context.say("zZzzzZzz...")

        self.context.sleep.sub(step)

    def on_message(self, telegram: Telegram):
        if telegram.message == MessageTypes.MSG_MEETING:
            self.context.describe("briefly awoken by his phone")
            return True
        if telegram.message == MessageTypes.MSG_WAKEUP:
            print("*BEEPBEEPBEEPBEEPBEEP*")
            self.context.say("Aarrghhlleblaarghl, already??")
            self.context.change_state(WorkState())
        return False

class EatState(AgentState):

    state_name = "a bite"
    state_verb = "eating"

    def enter(self):
        if self.context.is_at("dallas"):
            self.context.say("I am hungry, I want some lasagna")
        else:
            self.context.goto("dallas")

    def exit(self):
        self.context.describe("full!")

    def execute(self, step):

        if randint(0, self.context.hunger.max) == 1: self.context.say("Crunch!")
        
        self.context.hunger.sub(2 * step)
        
        if self.context.hunger.is_min:
            self.context.change_state(DrinkState())
            return

        if self.context.social.is_max:
            self.context.say("Oi oi, anyone wanna meet up at Dallas?")
            self.context.social.sub(randint(5, 10))
            msg = Telegram(self.context.id, None, MessageTypes.MSG_MEETING, "dallas")
            self.context.world.dispatch(0, msg)

class DrinkState(AgentState):

    state_name = "a drink"
    state_verb = "having a drink"

    def enter(self):
        if self.context.is_at("travven"):
            cost = randint(30, 60)
            self.context.describe("crackin' open a cold'un ({}:-)".format(cost))
            self.context.money -= cost
        else:
            self.context.goto("travven")

    def exit(self):
        self.context.describe("finishing his drink")

    def execute(self, step):

        if randint(0, self.context.thirst.max) == 1: self.context.say("Slurp!")
        
        self.context.thirst.sub(2 * step)
        self.context.drunk.add(3 * step)
        self.context.bladder.add(1 * step)

        if self.context.social.is_max:
            self.context.say("Hey guys! Come have a drink with me!")
            self.context.social.sub(randint(5, 10))
            msg = Telegram(self.context.id, None, MessageTypes.MSG_MEETING, "travven")
            self.context.world.dispatch(0, msg)

        if self.context.thirst.is_min:
            self.context.change_state(SleepState())
            return


class ToiletState(AgentState):

    def enter(self):
        self.context.say("Ooh, better hit the john!")

    def exit(self):
        self.context.say("That's better! Where were I?")

    def execute(self, step):

        self.context.bladder.set(0)
        self.context.revert_state()

class MeetingState(AgentState):

    state_name = "a meeting"
    state_verb = "meeting"

    _place = None
    _friends = []
    _phrases = [
        ("Drinking wine is like looking into the eye of a duck","And sucking all the fluids... from its beak"),
        ("You've got something between your teeth","Oh, but you have something between your ears!"),
        ("Didya read that book I told you about?","I barely have time to live as it is"),
        ("How was work today, then?","Just about as terrible as usual"),
        ("Can't wait for the Kravallsittning","Kravall 2020 babyyy!"),
        ("What's that smell?","Perhaps your nose is too close to your mouth"),
        ("Is that weird dude still staring at me?","Where?"),
        ("God, my tooth hurts!","Go see a dentist, then"),
        ("I love art - especially late... art","I like how the cow is looking off the side of the painting"),
        ("I've been playing a lot of INFRA lately","I don't want to hear another word about INFRA")
    ]

    def __init__(self, place):
        self._place = place
        self._friends = []

    def enter(self):
        if self._place is not None:
            if self.context.is_at(self._place):
                arrival_msg = Telegram(self.context.id, None, MessageTypes.MSG_ARRIVAL, self.context.location)
                self.context.world.dispatch(0, arrival_msg)
            else: 
                self.context.goto(self._place, self)            

    def execute(self, step):

        friend_count = len(self._friends)

        if friend_count > 0:
            friend = self._friends[randint(0, friend_count - 1)]
            phrase = self._phrases[randint(0, len(self._phrases) - 1)]
            self.context.say_to(friend, phrase[0])
            friend.say_to(self.context, phrase[1])
            self.context.social.sub(2 * step)
            friend.social.sub(2 * step)

            if self.context.social.is_min:
                self.context.say("Well, it's been fun, but I should get going!")
                self.context.revert_state()
                leave_msg = Telegram(self.context.id, None, MessageTypes.MSG_MEETING_LEAVING)
                self.context.world.dispatch(0, leave_msg)

    def on_message(self, telegram: Telegram):

        agent = self.context.world.get_agent(telegram.sender_id)

        if telegram.message == MessageTypes.MSG_MEETING_CANCEL:
            self.context.say("That's a shame. Catch you later, then!")
            self.context.revert_state()
            return True

        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == self.context.location:
            self.context.say("Hey {}! Glad you could make it".format(agent.name))
            self._friends.append(agent)
            return True

        if telegram.message == MessageTypes.MSG_MEETING_LEAVING:
            self.context.say_to(agent, "It's been fun, see you around!")
            if agent in self._friends:
                self._friends.remove(agent)
            if len(self._friends) == 0:
                self.context.say("Well, guess I should get going as well...")
                self.context.revert_state()
            return True


