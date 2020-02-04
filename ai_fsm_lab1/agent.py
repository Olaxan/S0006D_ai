import copy

from state import State, StateContext
from random import randint, seed
from world import World
from telegram import Telegram, MessageTypes
from utils import Clamped

# Autonomous agent, with stats, name, and location in world
class Agent(StateContext):

    _location = [0, 0]
    _world = None
    _id = 0

    name = "Agent"
    home    = None
    work    = None
    speed   = 0

    money   = None
    drunk   = None
    sleep   = None
    hunger  = None
    social  = None
    thirst  = None
    bladder = None

    def __init__(self, world: World, name: str, home: str, work: str):
        super().__init__(SleepState(), GlobalState())
        self._world = world
        self._location = [0, 0]

        self.name = name
        self.home = home
        self.work = work
        self.speed = randint(3, 5)
        
        self.money   = 0
        self.drunk   = Clamped(0, 0)
        self.sleep   = Clamped(7, 0, 8)
        self.bladder = Clamped(randint(0, 5), 0, 10)
        self.hunger  = Clamped(randint(0, 3), 0, 5)
        self.thirst  = Clamped(randint(0, 3), 0, 5)
        self.social  = Clamped(randint(0, 5), 0, 10)
        
        self._id = self._world.register_agent(self)

    def __del__(self):
        self.describe("dead")

    # Gets called by world manager, just before receiving an ID
    # For delayed initalization of variables that need reference to World
    def init(self):
        self.location = copy.copy(self.world.get_location(self.home)) # The agent should begin at home

    # Returns whether the agent is at the specified location
    # Takes a location name
    def is_at(self, location: str) -> bool:
        return self._world.is_at(self, location)

    # Returns whether two agents are on the same place in the World
    def is_near(self, other) -> bool:
        return self._location == other._location

    # Places the agent in a "goto"-state, moving them in the World
    def goto(self, location: str, on_arrive: State = None):

        if on_arrive is None: on_arrive = self._current_state

        target = self.world.get_location(location)
        eta = GotoState.estimate(self.location, target, self.speed)

        self.describe("going to {} for {} (ETA: {})".format(location.capitalize(), on_arrive.state_name, World.time_format_24(self.world.time + eta)))
        self.change_state(GotoState(target, self.speed, on_arrive), False, False)

    # Describes an action in, the form of "[HH:MM] Agent is ...""
    def describe(self, action):
        print("[{}] {} is {}".format(self.world.time_24, self.name, action))

    # Describes what the agent is saying, in the form of "[HH:MM] Agent: '...'""
    def say(self, phrase):
        if self.drunk.is_min:
            print("[{}] {}: '{}'".format(self.world.time_24, self.name, phrase))
        else:
            print("[{}] {}: '*hic!* {}'".format(self.world.time_24, self.name, phrase))

    # Describes what the agent is saying to someone else, in the form of "[HH:MM] Agent, to Agent: '...'"
    def say_to(self, other, phrase):
        if self.drunk.is_min:
            print("[{}] {}, to {}: '{}'".format(self.world.time_24, self.name, other.name, phrase))
        else:
            print("[{}] {}, to {}: '*hic!* {}'".format(self.world.time_24, self.name, other.name, phrase))

    @property   # Returns agent ID, immutable
    def id(self):
        return self._id

    @property   # Returns agent World, immutable
    def world(self):
        return self._world

    @property   # Returns agent's X position in World
    def x(self):
        return self._location[0]

    @x.setter
    def x(self, value):
        self._location[0] = value

    @property   # Returns agent's Y position in World
    def y(self):
        return self._location[1]

    @y.setter
    def y(self, value):
        self._location[1] = value

    @property   # Returns agent's [X, Y] position in World
    def location(self):
        return self._location

    @location.setter
    def location(self, location: [int, int]):
        self._location = location

# A specialized FSM state, containing flavor text, as well as providing an Agent context instead of StateContext
class AgentState(State):

    state_name = "unknown reasons"
    state_verb = "doing something"

    @property
    def context(self) -> Agent:
        return self._context

    @context.setter
    def context(self, context: Agent):
        self._context = context

# Move the agent to another place on the board
class GotoState(AgentState):

    _target = [0, 0]
    _on_arrive: None
    _speed = 1

    state_name = "a walk"
    state_verb = "walking"

    
    @staticmethod  # Estimate the time it will take to move to a new location in a straight line
    def estimate(location, target, speed):
        delta_x = abs(location[0] - target[0])
        delta_y = abs(location[1] - target[1])
        return max(delta_x / speed, delta_y / speed)

    def __init__(self, location: [int, int], speed = 1, on_arrive: State = None):
        self._on_arrive = on_arrive
        self._target = location
        self._speed = speed

    def _has_arrived(self, context) -> bool:
        return self._target[0] == context.x and self._target[1] == context.y

    def exit(self, context):
        if self._has_arrived(context):
            arrive_msg = Telegram(context.id, None, MessageTypes.MSG_ARRIVAL, context.location)
            context.world.dispatch(arrive_msg)

    def execute(self, context, step):

        if self._has_arrived(context):
            context.change_state(self._on_arrive) if self._on_arrive is not None else context.revert_state()
            return

        delta_x = self._target[0] - context.x
        if delta_x != 0:
            sign_x = delta_x / abs(delta_x)
            context.x += max(delta_x, sign_x * self._speed * step) if sign_x < 0 else min(delta_x, sign_x * self._speed * step)

        delta_y = self._target[1] - context.y
        if delta_y != 0:
            sign_y = delta_y / abs(delta_y)
            context.y += max(delta_y, sign_y * self._speed * step) if sign_y < 0 else min(delta_y, sign_y * self._speed * step)

    def on_message(self, context, telegram: Telegram):

        # Deny meeting messages while walking, just to avoid issues when "blipping" states several times
        # Might be removed in the future
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say("Sorry, I'm on my way somewhere!")
            reply_msg = Telegram(context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply_msg)
            return True
        return False

# A state with a common pool of participants, with the first member counting as host
class SharedState(AgentState):

    _party = None

    def __init__(self):
        self._party = []

    @property
    def count(self):
        return len(self._party)

    @property
    def host_id(self):
        return self._party[0].id if self.count > 0 else -1

    def join_state(self, agent, do_exit = True):
        self._party.append(agent)
        agent.change_state(self, do_exit=do_exit)

    def leave_state(self, agent):
        self._party.remove(agent)
        agent.revert_state()

class GlobalState(AgentState):

    rent = 2500

    def execute(self, context, step):
        context.drunk.sub(1 * step)
        context.social.add((randint(0, 5) == 1) * step)
        context.bladder.add((randint(0, 5) == 1) * step)

        if context.world.time % 240 == 0:
            context.describe("paying his rent ({}:-)".format(self.rent))
            context.money -= self.rent

        if context.bladder.is_max:
            context.change_state(ToiletState())
            return

    def on_message(self, context, telegram: Telegram):

        sender = context.world.get_agent(telegram.sender_id)

        # Retrieve a meeting invitation, and accept it based on social needs
        if telegram.message == MessageTypes.MSG_MEETING:
            if randint(0, context.social.max) <= context.social.current:
                eta = GotoState.estimate(context.location, context.world.get_location(telegram.data), context.speed)

                if context.location == sender.location:
                    context.say_to(sender, "I'm at {}, too! Hang on, let me come over".format(telegram.data.place.capitalize()))
                else:
                    context.say_to(sender, "You know it! I'm {} right now, but I'll be over in like {} minutes!".format(context.state.state_verb, int(60 * eta)))
                    
                reply_msg = Telegram(context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, True)
                context.world.dispatch(reply_msg)
                telegram.data.join_state(context)
            else:
                context.say("Sorry, not feeling it at the moment")
                reply_msg = Telegram(context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
                context.world.dispatch(reply_msg)

        # Chance to greet agents arriving to the same location
        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == context.location and randint(0, 4) == 1:
            context.say_to(sender, "Hey {}!".format(sender.name))

# Work between start and end hours, giving the agent money in the process
# Has specialized blip states for managing other needs while at work
class WorkState(AgentState):

    state_name = "work"
    state_verb = "working"
    start_hour = 8.5
    end_hour = 17
    pay = 120

    def enter(self, context):
        if context.is_at(context.work):
            if context.world.hour_24 <= self.start_hour:
                if context.world.time > self.start_hour:
                    context.say("Oh, running a bit late...")
                else:
                    context.say("Back in the hamster wheel")
            else:
                context.say("Well, back at it")
        else:
            context.goto(context.work)

    def exit(self, context):
        if context.world.hour_24 >= self.end_hour:
            context.say("Finally!")
        else:
            context.say("Just {0} hours left...".format(self.end_hour - context.world.hour_24))

    def execute(self, context, step):

        context.money += self.pay * step
        context.thirst.add(2 * step)
        context.sleep.add(2 * step)
        context.hunger.add(1 * step)

        if randint(0, int(self.end_hour - self.start_hour)) == 1:
            context.say("Ka-ching! Got {}:- now!".format(context.money))

        if context.world.hour_24 >= self.end_hour:
            context.change_state(EatState())
            return

        if context.sleep.is_max:
            context.change_state(WorkSleepState())
            return

        if context.thirst.is_max:
            context.change_state(WorkDrinkState())
            return

        if context.hunger.is_max:
            context.change_state(WorkEatState())
            return

    def on_message(self, context, telegram: Telegram):

        # Deny meeting requests on account of being at work
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say("Ah, naw mate, sorry, can't meet right now, I'm at work!")
            reply = Telegram(context.id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply)
            return True
        return False

# State for eating while at work
class WorkEatState(AgentState):

    state_name = "a sandwich"
    state_verb = "eating a sandwich"
    ignore_global = True
    sandwich_units = 5
    cost = 50

    def enter(self, context):
        context.describe("getting out his lunch from his bag ({}:-)".format(self.cost))
        context.money -= self.cost

    def exit(self, context):
        context.describe("returning to work")

    def execute(self, context, step):
        
        if randint(0, context.hunger.max) == 1: context.say("Krunch!")

        context.hunger.sub(self.sandwich_units)
        context.revert_state()

# State for drinking while at work
class WorkDrinkState(AgentState):

    state_name = "a sip of water"
    state_verb = "having a water break"
    ignore_global = True

    def enter(self, context):
        context.describe("going to the loo for a sip of water")

    def exit(self, context):
        context.describe("returning to work")

    def execute(self, context, step):
        
        if randint(0, context.thirst.max) == 1: context.say("Slurp!")

        context.thirst.sub(10)
        context.bladder.add(1)

        if context.thirst.is_min:
            context.revert_state()

# State for managing sleep by means of coffee while at work
class WorkSleepState(AgentState):

    state_name = "a cup of coffee"
    state_verb = "having a cuppa"
    ignore_global = True
    coffee_units = 3
    cost = 10

    def enter(self, context):
        context.describe("going to the breakroom for some coffee ({}:-)".format(self.cost))
        context.money -= self.cost


    def exit(self, context):
        context.describe("returning to work")

    def execute(self, context, step):
        
        if randint(0, context.sleep.max) == 1: context.say("Sörpl!")

        context.sleep.sub(self.coffee_units)
        context.bladder.add(1)

        context.revert_state()

# State for going to bed and sleeping until wakeup call
class SleepState(AgentState):

    state_name = "some sleep"
    state_verb = "sleeping"

    def enter(self, context):
        if context.is_at(context.home):
            # Dispatch delayed message to self in order to wake up in time for work
            wakeup_time = WorkState.start_hour - GotoState.estimate(context.location, context.world.get_location(context.work), context.speed) - 0.25
            context.say("Time for a nap - I'm an agent who loves to snooze")
            context.say("Lessee, I have to wake up at around... {0}!".format(World.time_format_24(wakeup_time)))
            alarm = Telegram(context.id, context.id, MessageTypes.MSG_WAKEUP)
            context.world.dispatch_scheduled(wakeup_time, alarm)
        else:
            context.goto(context.home)

    def exit(self, context):
        context.describe("waking up")

    def execute(self, context, step):
        if randint(0, context.sleep.max) == 1: context.say("zZzzzZzz...")
        context.sleep.sub(step)

    def on_message(self, context, telegram: Telegram):
        if telegram.message == MessageTypes.MSG_MEETING:
            context.describe("briefly awoken by his phone")
            return True
        if telegram.message == MessageTypes.MSG_WAKEUP:
            print("*BEEPBEEPBEEPBEEPBEEP*")
            context.say("Aarrghhlleblaarghl, already??")
            context.change_state(WorkState())
            return True
        return False

# State for going to Dallas for a meal
class EatState(AgentState):

    state_name = "a bite"
    state_verb = "eating"

    cost = 80

    has_invited = False

    def enter(self, context):
        if context.is_at("dallas"):
            context.describe("ordering a plate of kebab ({}:-)".format(self.cost))
            context.money -= self.cost
        else:
            context.goto("dallas")

    def exit(self, context):
        context.describe("finishing his meal")

    def execute(self, context, step):

        if randint(0, context.hunger.max) == 1: context.say("Crunch!")
        
        context.hunger.sub(2 * step)
        
        if context.hunger.is_min:
            context.change_state(DrinkState())
            return

        # If feeling lonely, call for friends to join
        if context.social.is_max and not self.has_invited:
            self.has_invited = True
            context.say("Anyone wanna meet up at Dallas?")
            meeting = MeetingState("dallas")
            meeting.join_state(context, do_exit=False)

# State for going to Travven for a drink
class DrinkState(AgentState):

    state_name = "a drink"
    state_verb = "having a drink"

    has_invited = False

    def enter(self, context):
        if context.is_at("travven"):
            cost = randint(30, 60)
            context.describe("crackin' open a cold'un ({}:-)".format(cost))
            context.money -= cost
        else:
            context.goto("travven")

    def exit(self, context):
        context.describe("finishing his drink")

    def execute(self, context, step):

        if randint(0, context.thirst.max) == 1: context.say("Slurp!")
        
        context.thirst.sub(2 * step)
        context.drunk.add(3 * step)
        context.bladder.add(1 * step)

        # If feeling lonely, call for friends to join you
        if context.social.is_max and not self.has_invited:
            self.has_invited = True
            context.say("Hey guys! Come have a drink with me!")
            meeting = MeetingState("travven")
            meeting.join_state(context, do_exit=False)

        if context.thirst.is_min:
            context.change_state(SleepState())
            return

# Blip state for going to bathroom
class ToiletState(AgentState):

    def enter(self, context):
        context.say("Ooh, better hit the john!")

    def exit(self, context):
        context.say("That's better! Where were I?")

    def execute(self, context, step):

        context.bladder.set(0)
        context.revert_state()

# Shared state for managing conversation during a meeting
class MeetingState(SharedState):

    state_name = "a meeting"
    state_verb = "meeting"

    _place = None
    _invitations = 0
    _replies = 0

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

    @property
    def place(self):
        return self._place

    def __init__(self, place):
        super().__init__()
        self._place = place
        self._invitations = 0
        self._replies = 0

    def enter(self, context):
        if self.count == 1:
            meet_msg = Telegram(context.id, None, MessageTypes.MSG_MEETING, self)
            self._invitations = context.world.dispatch(meet_msg)

        if self._place is not None and not context.is_at(self._place):
            context.goto(self._place, self)     

    def execute(self, context, step):

        # If agent is alone in group after receiving all replies from all, leave the group
        if self._replies >= self._invitations and self.count == 1:
            context.say("Oh, well...")
            self.leave_state(context)
            return

        # If agent is socially satisfied, leave the group and broadcast your departure
        if context.social.is_min:
            context.say("I really should get going!")
            leave_msg = Telegram(context.id, self.host_id, MessageTypes.MSG_MEETING_LEAVING)
            context.world.dispatch(leave_msg)
            self.leave_state(context)
            return

        # If more than one person is in the group, perform a conversation
        if self.count > 1:
            partner = self._party[randint(0, self.count - 1)]
            if partner is not context and partner.is_near(context):
                phrase = self._phrases[randint(0, len(self._phrases) - 1)]
                context.say_to(partner, phrase[0])
                partner.say_to(context, phrase[1])
                context.social.sub(2)
                partner.social.sub(2)
            return

    def on_message(self, context, telegram: Telegram):

        sender = context.world.get_agent(telegram.sender_id)

        # Decline meeting invitations on account of already being with friends
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say_to(sender, "Sorry, I'm already with some friends!")
            reply_msg = Telegram(context.id, sender.id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply_msg)
            return True

        # Count replies to your invitation
        if telegram.message == MessageTypes.MSG_MEETING_REPLY:
            self._replies += 1
            if telegram.data == True:
                if self.count == 1:
                    context.say("Sick! I'll be waiting")
                else:
                    context.say("The more the merrier!")
            else: 
                context.say("Some other time, then!")
            return True

        # Remove cancelled invitations from meeting
        if telegram.message == MessageTypes.MSG_MEETING_CANCEL:
            self._invitations -= 1
            context.say_to(sender, "That's a shame. Catch you later, then!")
            return True

        # Greet new arrivals to the group
        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == context.location and sender in self._party:
            context.say_to(sender, "Hey {}! Glad you could make it".format(sender.name))
            return True

        # Say goodbye to departing members, and return to previous state if now alone
        if telegram.message == MessageTypes.MSG_MEETING_LEAVING and sender.is_near(context):
            if self.count == 1:
                context.say("Well, guess I should get going as well...")
                self.leave_state(context)
            else:
                context.say_to(sender, "It's been fun, see you around!")
            return True

        return False


