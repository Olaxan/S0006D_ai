import collections, heapq
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
        cost = self.weights.get(node, self.default)
        return self.edges[node], cost

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

    def neighbours(self, cell):
        (x, y) = cell
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
        results = filter(self.is_in_bounds, results)
        results = filter(self.is_free, results)
        results = filter(lambda test: self.is_adjacent_free(test, cell), results)
        return results

class WeightedGrid(Grid):

    def __init__(self, width, height, walls=None, weights=None, default=1):
        super().__init__(width, height, walls)
        self.weights = weights if weights is not None else {}
        self.default = default

    def cost(self, cell):
        return self.weights.get(cell, self.default)

def reconstruct(node_map, start, goal):
    node = goal
    path = []
    while node is not start:
        path.append(node)
        node = node_map[node]
    path.append(start)
    path.reverse()
    return path

def brute_force_search(graph, start, goal, width_first=False):
    edges = QStack(width_first)
    edges.put(start)
    node_map = {}
    node_map[start] = None
    while not edges.is_empty:
        node = edges.pop()

        if node is goal:
            break

        for next_node in graph.neighbours(node):
            if next_node not in node_map:
                edges.put(next_node)
                node_map[next_node] = node

    return reconstruct(node_map, start, goal)

def manhattan(start, goal):
    x1, y1 = start
    x2, y2 = goal
    return abs(x2 - x1) + abs(y2 - y1)

def a_star_search(graph, start, goal, heuristic):
    edges = PriorityQueue()
    edges.put(start, 0)
    came_from = {start: None}
    cost_map = {start: 0}

    while not edges.is_empty:
        node = edges.pop()

        if node == goal:
            return True, reconstruct(came_from, start, goal)

        for next_node in graph.neighbours(node):
            next_cost = cost_map[node] + graph.cost(next_node)
            if next_node not in cost_map or next_cost < cost_map[next_node]:
                cost_map[next_node] = next_cost
                priority = next_cost + heuristic(goal, next_node)
                edges.put(next_node, priority)
                came_from[next_node] = node

    return False, None
