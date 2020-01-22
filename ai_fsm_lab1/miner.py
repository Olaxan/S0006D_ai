from state import State, StateContext

class Miner(StateContext):

    def __init__(self, initial: StateContext, id: int, name: str):
        super().__init__(initial, id)
        self.name = name

    name = "Miner"
    tiredness = 100
    hunger = 0

class MinerState(State):

    @property
    def context(self) -> Miner:
        return self._context

    @context.setter
    def context(self, context: Miner) -> None:
        self._context = context

class IdleState(MinerState):

    def enter(self):
        pass

    def exit(self):
        pass

    def execute(self):
        if (self.context.hunger > 80):
            self.context.changeState(EatState())
        elif (self.context.tiredness > 80):
            self.context.changeState(SleepState())
        else:
            print(self.context.name, "is twiddling their thumbs")

class SleepState(MinerState):

    def enter(self):
        print(self.context.name, "is fast asleep")

    def exit(self):
        print(self.context.name, "wakes up")

    def execute(self):
        if (self.context.tiredness > 0):
            print(self.context.tiredness)
            self.context.tiredness -= 2
            self.context.hunger += 1
        else:
            self.context.changeState(IdleState())

class EatState(MinerState):

    def enter(self):
        print(self.context.name, "is cooking something strange")

    def exit(self):
        print(self.context.name, "is propp full")

    def execute(self):
        if (self.context.hunger > 0):
            self.context.hunger -= 2
            self.context.tiredness += 1
        else:
            self.context.changeState(IdleState())
