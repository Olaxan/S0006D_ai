from random import randint, choice
from state import State, StateContext
from world import World
from telegram import Telegram, MessageTypes
from utils import Clamped
from path import Path

# Autonomous agent, with stats, name, and location in world
class Agent(StateContext):

    _location = [0, 0]
    _world = None
    _id = 0

    def __init__(self, world: World, name: str, home: str, work: str):
        super().__init__(SleepState(), GlobalState())
        self._world = world
        self._location = [0, 0]

        self.name = name
        self.home = home
        self.work = work
        self.speed = randint(10, 15)

        self.money = randint(2500, 10000)
        self.drunk = Clamped(0, 0)
        self.sleep = Clamped(7, 0, 8)
        self.bladder = Clamped(randint(0, 5), 0, 10)
        self.hunger = Clamped(randint(0, 3), 0, 5)
        self.thirst = Clamped(randint(0, 3), 0, 5)
        self.social = Clamped(randint(0, 5), 0, 10)

        self._id = self._world.register_agent(self)

    def __del__(self):
        self.describe("dead")

    # Gets called by world manager, just before receiving an agent_id
    # For delayed initalization of variables that need reference to World
    def init(self):
        x, y = self.world.get_location(self.home)
        self.location = [x, y] # The agent should begin at home

    # Returns whether the agent is at the specified location
    # Takes a location name
    def is_at(self, location: str) -> bool:
        return self._world.is_at(self, location)

    # Returns whether two agents are on the same place in the World
    def is_near(self, other) -> bool:
        return self.location == other.location

    # Places the agent in a "goto"-state, moving them in the World
    def goto(self, location: str, on_arrive=None):

        if on_arrive is None:
            on_arrive = self._current_state

        target = self.world.get_location(location)
        eta = GotoState.estimate(self, self.location, target)

        self.describe("going to {} for {} (ETA: {})".format(location.capitalize(), on_arrive.state_name, World.time_format_24(self.world.time + eta)))
        self.change_state(GotoState(target, on_arrive, PathErrorState()), do_exit=False)

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

    @property   # Returns agent agent_id, immutable
    def agent_id(self):
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
        return self.x, self.y

    @location.setter
    def location(self, location):
        x, y = location
        self._location = [x, y]

    @property
    def is_walking(self) -> bool:
        return isinstance(self.state, GotoState)

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

    state_name = "a walk"
    state_verb = "walking"

    revertable = False

    meeting_refuse = [
        "Sorry, I'm on my way somewhere!",
        "No can do, sorry!",
        "Busy unfortunately",
        "Maybe some other day?",
        "Ah, I'd love to, but try me again in a few hours"
    ]

    @staticmethod  # Estimate the time it will take to move to a new location using a-star
    def estimate(context, location, target):
        success, path = context.world.get_path(location, target)
        return len(path) / context.speed if success else -1

    def __init__(self, location, on_arrive=None, on_fail=None):
        self._on_arrive = on_arrive
        self._on_fail = on_fail
        self._target = location
        self._path = []
        self._progress = 0

    def _has_arrived(self, context) -> bool:
        """Check if agent has arrived at target"""
        return self._target[0] == context.x and self._target[1] == context.y

    def _finish(self, context):
        """Call once agent is finished with path, to change state appropriately"""
        if self._on_arrive is not None:
            context.change_state(self._on_arrive)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_ARRIVAL, context.location)
        context.world.dispatch(arrive_msg)

    def _abort(self, context):
        """Call if agent failed pathing, to revert states appropriately"""
        if self._on_fail is not None:
            context.change_state(self._on_fail)
        else:
            context.revert_state()

        arrive_msg = Telegram(context.agent_id, None, MessageTypes.MSG_PATH_FAIL, context.location)
        context.world.dispatch(arrive_msg)

    def enter(self, context):
        success, self._path = context.world.get_path(context.location, self._target)
        if not success:
            self._abort(context)

    def execute(self, context, step):

        path_len = len(self._path)

        if path_len > 0:
            self._progress += context.speed * step
            if self._progress >= path_len:
                context.location = self._path[-1]
                self._finish(context)
            else:
                context.location = self._path[int(self._progress)]
            return

        # If the execute function is performed with no valid path, use legacy movement system.
        if self._has_arrived(context):
            self._finish(context)

        delta_x = self._target[0] - context.x
        if delta_x != 0:
            sign_x = delta_x / abs(delta_x)
            context.x += max(delta_x, sign_x * context.speed * step) if sign_x < 0 else min(delta_x, sign_x * context.speed * step)

        delta_y = self._target[1] - context.y
        if delta_y != 0:
            sign_y = delta_y / abs(delta_y)
            context.y += max(delta_y, sign_y * context.speed * step) if sign_y < 0 else min(delta_y, sign_y * context.speed * step)

    def on_message(self, context, telegram: Telegram):

        sender = context.world.get_agent(telegram.sender_id)

        # Deny meeting messages while walking, just to avoid issues when "blipping" states several times
        # Might be removed in the future
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say_to(sender, choice(self.meeting_refuse))
            reply_msg = Telegram(context.agent_id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply_msg)
            return True
        return False

    @property
    def path(self):
        return self._path

    @property
    def valid(self):
        return len(self._path) > 0

class PathErrorState(AgentState):

    def enter(self, context):
        context.describe("placed in a path error state!")

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
        return self._party[0].agent_id if self.count > 0 else -1

    def join_state(self, agent, do_exit=True):
        self._party.append(agent)
        agent.change_state(self, do_exit=do_exit)

    def leave_state(self, agent, state=None):
        if agent in self._party:
            self._party.remove(agent)
        if state is None:
            agent.revert_state()
        else:
            agent.change_state(state)

class GlobalState(AgentState):

    rent = 2500

    meeting_same_location = [
        "I'm already at {}, can't you see me? Hang on!",
        "I'm at {}, too! Hang on, let me come over",
        "At {}? But I'm already here! Hey!",
        "Well well well, having a {}-day, are we?"
    ]

    meeting_other_location = [
        "You know it! I'm {0} right now, but I'll be over in like {1} minutes!",
        "Sure! I'm about {1} minutes away, {0} right now",
        "Be there soon! I'm {0}, should be there in about {1}"
    ]

    meeting_refuse = [
        "Nah man, I'm knackered!",
        "Can't be arsed at the moment, sorry",
        "Have to take a rain-check on that!",
        "Sorry, not feeling it at the moment",
        "Oooh, can't work that into my schedule, sorry!"
    ]

    greetings = [
        "Ahoy hoy, {}!",
        "Good to see you, {}",
        "If it isn't {}",
        "Fancy seeing you here, {}!",
        "'aight, {}?",
        "Hey {}!"
    ]

    def execute(self, context, step):

        context.drunk.sub(1 * step)
        context.social.add((randint(0, 5) == 1) * step)
        context.bladder.add((randint(0, 5) == 1) * step)

        if (context.world.time - 24) % 720 == 0:
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
                eta = GotoState.estimate(context, context.location, context.world.get_location(telegram.data))

                if context.location == sender.location:
                    context.say_to(sender, choice(self.meeting_same_location).format(telegram.data.place.capitalize()))
                else:
                    context.say_to(sender, choice(self.meeting_other_location).format(context.state.state_verb, int(60 * eta)))

                reply_msg = Telegram(context.agent_id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, True)
                context.world.dispatch(reply_msg)
                telegram.data.join_state(context)
            else:
                context.say(choice(self.meeting_refuse))
                reply_msg = Telegram(context.agent_id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
                context.world.dispatch(reply_msg)

        # Chance to greet agents arriving to the same location
        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == context.location and randint(0, 4) == 1:
            context.say_to(sender, choice(self.greetings).format(sender.name))

# Work between start and end hours, giving the agent money in the process
# Has specialized blip states for managing other needs while at work
class WorkState(AgentState):

    state_name = "work"
    state_verb = "working"
    start_hour = 8.5
    end_hour = 17
    pay = 120

    running_late = [
        "Late again...",
        "Should've set my alarm earlier",
        "Boss is gonna kill me",
        "Good thing nobody sees me arriving this late...",
        "Good grief, already so late?",
        "Oh, running a bit late..."
    ]

    starting_work = [
        "Back to running in the hamster wheel",
        "Another day, another Swedish Krona",
        "Hope today won't be too busy",
        "Shit, where's my work ID?",
        "God, I hate this job",
        "Feeling pretty good about working today!",
        "Dreading having to work, today..."
    ]

    returning_work = [
        "Well, back at it",
        "Break's over, I suppose",
        "Alright, alright, I'm working...",
        "Hope the rest of the day goes quickly"
    ]

    stopping_work = [
        "Finally!",
        "Hooray!",
        "I'm out!",
        "Thank god that's done with",
        "Today went by like a flash!",
        "Longest day of my life..."
    ]

    hours_left = [
        "Just {} hours left...",
        "{} hours... Christ",
        "That's {} more hours, then",
        "Not too long left, just {} hours",
        "{} hours! Has the clock stopped?",
    ]

    earn_money = [
        "Ka-ching! Got {}:- now!",
        "Looks like I have {}:- in my account",
        "{}:-! I'll have that boat in no-time",
        "Sweet, up to {}:-"
    ]

    meeting_refuse = [
        "Ah, naw mate, sorry, can't meet right now, I'm at work!",
        "I'd love to, but I'm at work",
        "Aren't you at work?",
        "I'm working, maybe afterwards if you're still there!"
    ]

    def enter(self, context):
        if context.is_at(context.work):
            if context.world.hour_24 <= self.start_hour:
                if context.world.time > self.start_hour:
                    context.say(choice(self.running_late))
                else:
                    context.say(choice(self.starting_work))
            else:
                context.say(choice(self.returning_work))
        else:
            context.goto(context.work)

    def exit(self, context):
        if context.world.hour_24 >= self.end_hour:
            context.say(choice(self.stopping_work))
        else:
            context.say(choice(self.hours_left).format(self.end_hour - context.world.hour_24))

    def execute(self, context, step):

        context.money += self.pay * step
        context.thirst.add(2 * step)
        context.sleep.add(2 * step)
        context.hunger.add(1 * step)

        if randint(0, int(self.end_hour - self.start_hour)) == 1:
            context.say(choice(self.earn_money).format(context.money))

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

        sender = context.world.get_agent(telegram.sender_id)

        # Deny meeting requests on account of being at work
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say_to(sender, choice(self.meeting_refuse))
            reply = Telegram(context.agent_id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
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

    starting_sleep = [
        "Time for a nap - I'm an agent who loves to snooze",
        "God, I'm dead tired",
        "Aaah, I've been waiting for this all day",
        "To dreamland I go!",
        "I'm knackered!",
        "I've never been so tired in my life!"
    ]

    set_alarm = [
        "Lessee, I have to wake up at around... {}!",
        "Setting an alarm for {}",
        "{}! Too early!",
        "I'll have to wake up at {} if I want to make it in time",
        "{} should be plenty of time",
        "Hmmm, I'll set the alarm to {}"
    ]

    sleeping = [
        "ZzzZzzZ...",
        "ZzzZzzZzzzzzz!",
        "ZzzzzZzzzZzZZZz...",
        "*SNORK!*",
        "*Yawn*",
        "Ahghhzzzzzz..."
    ]

    stopping_sleep = [
        "Aarrghhlleblaarghl, already??",
        "Nooo, I was having such a nice dream!",
        "What, already morning?",
        "I barely slept at all...",
        "Wow, I feel great!",
        "Bloody... woke me up... fah!",
        "Gonna make a million, never work again...",
        "*YAAAAWN*"
    ]

    alarm = [
        "*BEEP BEEP BEEP BEEP BEEP*",
        "*WAKE UP! GRAB THE BRUSH AND PUT ON A LITTLE MAKEUP!*",
        "*Riiiiiiiiiing!*",
        "*Beepity beepity beep!*",
        "*Good morning everyone! Radio 4 here with the weather...*"
    ]

    def enter(self, context):
        if context.is_at(context.home):
            # Dispatch delayed message to self in order to wake up in time for work
            wakeup_time = WorkState.start_hour - GotoState.estimate(context, context.location, context.world.get_location(context.work)) - 0.25
            context.say(choice(self.starting_sleep))
            context.say(choice(self.set_alarm).format(World.time_format_24(wakeup_time)))
            alarm = Telegram(context.agent_id, context.agent_id, MessageTypes.MSG_WAKEUP)
            context.world.dispatch_scheduled(wakeup_time, alarm)
        else:
            context.goto(context.home)

    def exit(self, context):
        context.describe("waking up")

    def execute(self, context, step):
        if randint(0, context.sleep.max) == 1: context.say(choice(self.sleeping))
        context.sleep.sub(step)

    def on_message(self, context, telegram: Telegram):
        if telegram.message == MessageTypes.MSG_MEETING:
            context.describe("briefly awoken by his phone")
            reply_msg = Telegram(context.agent_id, telegram.sender_id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply_msg)
            return True
        if telegram.message == MessageTypes.MSG_WAKEUP:
            print(choice(self.alarm))
            context.say(choice(self.stopping_sleep))
            context.change_state(WorkState())
            return True
        return False

# State for going to Dallas for a meal
class EatState(AgentState):

    state_name = "a bite"
    state_verb = "eating"

    cost = 80

    has_invited = False

    food_items = [
        ("plate of kebab", 80),
        ("pizza", 70),
        ("small cheese burger", 55),
        ("box of fries", 40),
        ("kebabrulle", 79)
    ]

    meeting_invite = [
        "Anyone wanna meet up at Dallas?",
        "Hey, anyone in the mood for some Dallas?",
        "Yo, come get some dinner with me!",
        "Anyone wanna do someting?",
        "Anybody fancy some kebab?"
    ]

    def enter(self, context):

        order = choice(self.food_items)

        if context.is_at("dallas"):
            context.describe("ordering a {} ({}:-)".format(order[0], order[1]))
            context.money -= order[1]
        else:
            context.goto("dallas")

    def exit(self, context):
        context.describe("finishing his meal")

    def execute(self, context, step):

        if randint(0, context.hunger.max) == 1:
            context.say("Crunch!")

        context.hunger.sub(2 * step)

        if context.hunger.is_min:
            context.change_state(DrinkState())
            return

        # If feeling lonely, call for friends to join
        if context.social.is_max and not self.has_invited:
            self.has_invited = True
            context.say(choice(self.meeting_invite))
            meeting = MeetingState("dallas")
            meeting.join_state(context, do_exit=False)

# State for going to Travven for a drink
class DrinkState(AgentState):

    state_name = "a drink"
    state_verb = "having a drink"

    has_invited = False

    beverages = [
        ("getting themselves a Sam Adams", 40),
        ("ordering a Budvar", 30),
        ("cracking open a lager", 45),
        ("getting a drink", 50),
        ("sipping on a whiskey", 60),
        ("having a gin-tonic", 50)
    ]

    meeting_invite = [
        "Hey guys! Come have a drink with me!",
        "Anyone wanna join me at Travven?",
        "Anybody coming to Travven?",
        "Hey, after-work?!",
        "Yo yo, come join me for a drink!",
        "Anyone free for a drink?",
        "Buy you a beer if you come to Travven"
    ]

    def enter(self, context):
        if context.is_at("travven"):
            order = choice(self.beverages)
            context.describe("{} ({}:-)".format(order[0], order[1]))
            context.money -= order[1]
        else:
            context.goto("travven")

    def exit(self, context):
        context.describe("finishing their drink")

    def execute(self, context, step):

        if randint(0, context.thirst.max) == 1: context.say("Slurp!")

        context.thirst.sub(2 * step)
        context.drunk.add(3 * step)
        context.bladder.add(1 * step)

        # If feeling lonely, call for friends to join you
        if context.social.is_max and not self.has_invited:
            self.has_invited = True
            context.say(choice(self.meeting_invite))
            meeting = MeetingState("travven")
            meeting.join_state(context, do_exit=False)

        if context.thirst.is_min:
            context.change_state(SleepState())
            return

# Blip state for going to bathroom
class ToiletState(AgentState):

    enter_bathroom = [
        "Ooh, better hit the john!",
        "I'm burstin'!",
        "Would you excuse me for one second?",
        "Be right back, just gotta take a leak",
        "Need to piss!",
        "Can't hold it in any longer!"
    ]

    exit_bathroom = [
        "That's better! Where were I?",
        "Ahhh... Back to business",
        "Back to whatever I was doing!",
        "God I love going to the bathroom",
        "That was one nasty urinal",
        "That hit the spot"
    ]

    def enter(self, context):
        context.say(choice(self.enter_bathroom))

    def exit(self, context):
        context.say(choice(self.exit_bathroom))

    def execute(self, context, step):

        context.bladder.set(0)
        context.revert_state()

# Shared state for managing conversation during a meeting
class MeetingState(SharedState):

    state_name = "a meeting"
    state_verb = "meeting"

    ignore_global = True

    _place = None
    _invitations = 0
    _replies = 0

    _phrases = [
        ["Drinking wine is like looking into the eye of a duck", [
            "And sucking all the fluids... from its beak",
            "You've had too much wine yourself, it seems!",
            "The colours, a- ALL the colours!",
            "Not much for wine, OR ducks, myself",
            "I'm more of a goose person",
            "Hate wine!"]
        ], ["You've got something between your teeth", [
            "Oh, but you have something between your ears!",
            "Oh, no! How long has that been there?",
            "Whoah, that's almost a whole sardine!",
            "Thanks for pointing that out!",
            "Cheerio!",
            "Hate popcorn!"]
        ], ["Didya read that book I told you about?", [
            "I barely have time to live as it is",
            "Dostojevskij really knew how to write!",
            "Yes, it's alright, I suppose",
            "Not much for sci-fi, but it's good so far",
            "With the DOA underway? No way José",
            "Hate books!"]
        ], ["How was work today, then?", [
            "Just about as terrible as usual",
            "Oh, alright I suppose...",
            "There was this really nasty lady...",
            "Can't complain!",
            "Not too shabby, how about you?",
            "Hate work!"]
        ], ["Can't wait for the Kravallsittning", [
            "Kravall 2020 babyyy!",
            "Oh shit, I have to buy a ticket!",
            "I have so many märken to sew on...",
            "I've been airing out my ovve for a week and it still smells like crayfish",
            "Hype",
            "I'm not going this year, I'll be out of town",
            "Love Kravall!"]
        ], ["What's that smell?", [
            "Perhaps your nose is too close to your mouth",
            "Smells like elderberries",
            "I don't know, but I don't like it",
            "Smells like food!",
            "Oh, sorry",
            "I hate it!"]
        ], ["Is that weird dude still staring at me?", [
            "Where?",
            "I think so...",
            "I don't know, who?",
            "What?",
            "Yep",
            "Wanna leave?",
            "Hate weird dudes!"]
        ], ["God, my tooth hurts!", [
            "Go see a dentist, then",
            "Stop chewing so hard",
            "How long has it been aching?",
            "That sucks",
            "Sorry to hear that",
            "Hate teeth!"]
        ], ["I love art - especially late... art", [
            "I like how the cow is looking off the side of the painting",
            "That's not art, that's grafitti",
            "Hate art!",
            "You pretentious plonker",
            "That's just the sign to the bathroom"]
        ], ["I've been playing a lot of INFRA lately", [
            "I don't want to hear another word about INFRA",
            "I honestly, truly, couldn't care less",
            "This again?",
            "Nooooo",
            "Oh, I love that game!",
            "Hate that game!"]
        ]
    ]

    _disband_group = [
        "Oh, well...",
        "I'll get going, then",
        "Back to business...",
        "It's getting late anyway",
        "*Yawn*"
    ]

    _leave_group = [
        "I really should get going!",
        "It's been a blast, but I need to leave",
        "Well, I'm outtahere, see you!",
        "Getting up early tomorrow, peace!",
        "It's that late already?! I need to leave!",
        "Been great seeing you, bye!"
    ]

    _meeting_refuse = [
        "Sorry, I'm already with some friends!",
        "Nah, we're a crowd down here - join us if you want!",
        "Already with some mates! Come over here instead!",
        "We're like, a bunch of people already",
        "Ah, busy at the moment, sorry!",
        "Oh, maybe after this!"
    ]

    _meeting_accepted_first = [
        "Fun! Be waiting for you",
        "Sick! I'll be waiting",
        "Hurry!",
        "See you in a bit!",
        "Sweet, catch you in a while then",
        "Eyyyyy!"
    ]

    _meeting_accepted_multi = [
        "The more the merrier!",
        "Great, come join us!",
        "Awesome! We're all waiting for you!",
        "We'll save a seat for you!"
    ]

    _meeting_refused = [
        "Some other time, then!",
        "Ah, gotcha",
        "That's a shame, later then!",
        "No worries, see you some other time",
        "Understandable! See you around!",
        "Aw man! Catch you later, then!"
    ]

    _meeting_welcome = [
        "Hey {}! Glad you could make it",
        "The man, the myth, the legend, {}!",
        "So good to see you, {}!",
        "Glad you could join us, {}!",
        "Eyo, {}!",
        "Hi, {}!",
        "Great to see you, {}!"
    ]

    _meeting_goodbye = [
        "It's been fun, see you around!",
        "Goodbye!",
        "It's been a blast! See you!",
        "See you later, alligator!",
        "Bye, bye!",
        "Have a good one!"
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
            meet_msg = Telegram(context.agent_id, None, MessageTypes.MSG_MEETING, self)
            self._invitations = context.world.dispatch(meet_msg)

        if self._place is not None and not context.is_at(self._place):
            context.goto(self._place)

    def execute(self, context, step):

        # print("MEETING: {} in party, host agent_id {}, {} invitations, {} replies\n[{}]".format(
        #     self.count, self.host_id, self._invitations, self._replies, ", ".join(list(agent.name for agent in self._party))
        # ))

        # If agent is alone in group after receiving all replies from all, leave the group
        if self._replies >= self._invitations and self.count == 1:
            context.say(choice(self._disband_group))
            self.leave_state(context, SleepState())
            return

        # If agent is socially satisfied, leave the group and broadcast your departure
        if context.social.is_min and self.host_id is not context.agent_id:
            context.say(choice(self._leave_group))
            leave_msg = Telegram(context.agent_id, self.host_id, MessageTypes.MSG_MEETING_LEAVING)
            context.world.dispatch(leave_msg)
            self.leave_state(context, SleepState())
            return

        # If more than one person is in the group, perform a conversation
        if self.count > 1:
            partner = self._party[randint(0, self.count - 1)]
            if partner is not context and partner.is_near(context):
                phrase = self._phrases[randint(0, len(self._phrases) - 1)]
                context.say_to(partner, phrase[0])
                partner.say_to(context, choice(phrase[1]))
                context.social.sub(2)
                partner.social.sub(2)
            return

    def on_message(self, context, telegram: Telegram):

        sender = context.world.get_agent(telegram.sender_id)

        # Decline meeting invitations on account of already being with friends
        if telegram.message == MessageTypes.MSG_MEETING:
            context.say_to(sender, choice(self._meeting_refuse))
            reply_msg = Telegram(context.agent_id, sender.agent_id, MessageTypes.MSG_MEETING_REPLY, False)
            context.world.dispatch(reply_msg)
            return True

        # Count replies to your invitation
        if telegram.message == MessageTypes.MSG_MEETING_REPLY:
            self._replies += 1
            if telegram.data:
                if self.count == 1:
                    context.say(choice(self._meeting_accepted_first))
                else:
                    context.say(choice(self._meeting_accepted_multi))
            else:
                context.say(choice(self._meeting_refused))
            return True

        # Remove cancelled invitations
        if telegram.message == MessageTypes.MSG_MEETING_CANCEL:
            self._invitations -= 1
            context.say_to(sender, choice(self._meeting_refused))
            return True

        # Greet new arrivals to the group
        if telegram.message == MessageTypes.MSG_ARRIVAL and telegram.data == context.location and sender in self._party:
            context.say_to(sender, choice(self._meeting_welcome).format(sender.name))
            return True

        # Say goodbye to departing members, and return to previous state if now alone
        if telegram.message == MessageTypes.MSG_MEETING_LEAVING and sender in self._party:
            if self.count == 1:
                context.say(choice(self._disband_group))
                self.leave_state(context)
            else:
                context.say_to(sender, choice(self._meeting_goodbye))
            return True

        return False


