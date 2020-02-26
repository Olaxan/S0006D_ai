from goap2 import Planner, Action, WorldState

actions = {
    Action("scout", 1, [("armedwithgun", True)], [("enemyvisible", True)]),
    Action("approach", 1, ["enemyvisible", True], ["nearenemy", True]),
    Action("aim", 1, [("enemyvisible", True), ("weaponloaded", True)], [("enemylinedup", True)]),
    Action("shoot", 5, [("enemylinedup", True)], [("enemyalive", False)]),
    Action("load", 2, [("armedwithgun", True)], [("weaponloaded, True")]),
    Action("detonatebomb", 10, [("armedwithbomb", True), ("nearenemy", True)], [("alive", False), ("enemyalive", False)]),
    Action("flee", 1, [("enemyvisible", True)], [("nearenemy", False)])
}

state = WorldState(
    {
        "enemyvisible":   False,
        "armedwithgun":   True,
        "weaponloaded":   False,
        "enemylinedup":   False,
        "enemyalive":     True,
        "armedwithbomb":  True,
        "nearenemy":      False,
        "alive":          True,
    }
)

goal = WorldState(
    {"enemyalive": False}
)

planner = Planner(actions, state)
planner.plan(goal)