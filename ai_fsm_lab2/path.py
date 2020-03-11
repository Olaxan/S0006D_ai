from __future__ import annotations
import collections
import heapq
from enum import Enum, auto

class QStack:

    def __init__(self, use_stack = False):
        self.queue = collections.deque()
        self._use_stack = use_stack

    @property
    def is_empty(self):
        return len(self.queue) == 0

    def put(self, element):
        self.queue.append(element)

    def pop(self):
        return self.queue.popleft() if self._use_stack else self.queue.pop()

class PriorityQueue:

    def __init__(self):
        self.heap = []

    @property
    def is_empty(self):
        return len(self.heap) == 0

    def put(self, element, priority=1):
        heapq.heappush(self.heap, (priority, element))

    def pop(self):
        return heapq.heappop(self.heap)[1]

class Graph:

    def __init__(self, edges=None):
        self.edges = edges if edges is not None else []

    def neighbours(self, node):
        return self.edges[node]

class WeightedGraph:

    def __init__(self, edges=None, weights=None, default=1):
        self.edges = edges if edges is not None else []
        self.weights = weights if weights is not None else {}
        self.default = default

    def neighbours(self, node):
        return self.edges[node]

    def cost(self, node):
        return self.weights.get(node, self.default)

class Grid:

    def __init__(self, width, height, walls=None):
        self.width = width
        self.height = height
        self.walls = walls if walls is not None else []

    def is_in_bounds(self, cell):
        (x, y) = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, cell):
        return cell not in self.walls

    def is_adjacent_free(self, from_cell, to_cell):
        dx = to_cell[0] - from_cell[0]
        dy = to_cell[1] - from_cell[1]
        return self.is_free((from_cell[0] + dx, from_cell[1])) and self.is_free((from_cell[0], from_cell[1] + dy))

    def neighbours(self, cell, is_free=True, filter_func=None):
        x, y = cell
        results = [
            (x + 1, y),     # right
            (x + 1, y - 1), # top right
            (x, y - 1),     # top
            (x - 1, y - 1), # top left
            (x - 1, y),     # left
            (x - 1, y + 1), # bottom left
            (x, y + 1),     # bottom
            (x + 1, y + 1)  # bottom right
        ]
        if is_free:
            results = filter(self.is_in_bounds, results)
            results = filter(self.is_free, results)
            results = filter(lambda test: self.is_adjacent_free(test, cell), results)
        if filter_func is not None:
            results = filter(filter_func, results)
        return results

class WeightedGrid(Grid):

    def __init__(self, width, height, walls=None, weights=None, default=1):
        super().__init__(width, height, walls)
        self.weights = weights if weights is not None else {}
        self.default = default

    def cost(self, cell):
        return self.weights.get(cell, self.default)

class Path:

    class Algorithms(Enum):
        A_STAR = auto()
        DEPTH_FIRST = auto()
        BREADTH_FIRST = auto()

    @staticmethod
    def reconstruct(node_map, start, goal):
        node = goal
        path = []

        while node is not start:
            path.append(node)
            node = node_map[node]
        path.append(start)
        path.reverse()
        return path

    @staticmethod
    def brute_force_search(graph, start, goal, breadth_first=False):

        if start == goal:
            return True, [goal]

        edges = QStack(breadth_first)
        edges.put(start)
        node_map = {}
        node_map[start] = None

        while not edges.is_empty:
            node = edges.pop()

            if node == goal:
                return True, Path.reconstruct(node_map, start, goal)

            for next_node in graph.neighbours(node):
                if next_node not in node_map:
                    edges.put(next_node)
                    node_map[next_node] = node

        return False, []

    @staticmethod
    def manhattan(node, goal):
        dx = abs(node[0] - goal[0])
        dy = abs(node[1] - goal[1])
        return dx + dy

    @staticmethod
    def diagonal(node, goal):
        dx = abs(node[0] - goal[0])
        dy = abs(node[1] - goal[1])
        return (dx + dy) + (1.4 - 2) * min(dx, dy)

    @staticmethod
    def a_star_search(graph, start, goal, cost_mult=1, heuristic=None, filter_func=None):
        """Performs a graph search using the A* algorithm.
        If no heuristic is provided, functions like Dijkstra's"""

        cost_map = {start: 0}
        came_from = {start: None}

        if start == goal:
            return True, [goal]

        edges = PriorityQueue()
        edges.put(start, 0)

        while not edges.is_empty:
            node = edges.pop()

            if node == goal:
                return True, Path.reconstruct(came_from, start, goal)

            for next_node in graph.neighbours(node, True, filter_func):
                next_cost = cost_map[node] + graph.cost(next_node)
                if next_node not in cost_map or next_cost < cost_map[next_node]:
                    cost_map[next_node] = next_cost
                    priority = next_cost

                    if heuristic is not None:
                        priority += cost_mult * heuristic(next_node, goal)

                    edges.put(next_node, priority)
                    came_from[next_node] = node

        return False, []

    @staticmethod
    def a_star_proxy(graph, start, goal, on_finish, cost_mult=1, heuristic=None, filter_func=None):
        success, path = Path.a_star_search(graph, start, goal, cost_mult, heuristic, filter_func)
        on_finish(success, path)

    @staticmethod
    def dijkstras_nearest(graph, start, goal_func, filter_func=None):

        cost_map = {start: 0}
        came_from = {start: None}

        if goal_func(start):
            return True, [start]

        edges = PriorityQueue()
        edges.put(start, 0)

        while not edges.is_empty:
            node = edges.pop()

            if goal_func(node):
                return True, Path.reconstruct(came_from, start, node)

            for next_node in graph.neighbours(node, True, filter_func):
                next_cost = cost_map[node] + graph.cost(next_node)
                if next_node not in cost_map or next_cost < cost_map[next_node]:
                    cost_map[next_node] = next_cost
                    priority = next_cost
                    edges.put(next_node, priority)
                    came_from[next_node] = node

        return False, []

    @staticmethod
    def dijkstras_proxy(graph, start, goal_func, on_finish, filter_func=None):
        success, path = Path.dijkstras_nearest(graph, start, goal_func, filter_func)
        on_finish(success, path)
