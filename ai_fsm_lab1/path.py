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

    def put(self, element, priority = 1):
        heapq.heappush(self.heap, (priority, element))

    def pop(self):
        return heapq.heappop(self.heap)[1]

class Graph:

    def __init__(self, edges = {}):
        self.edges = edges

    def neighbours(self, node):
        return self.edges[node]

class WeightedGraph:

    def __init__(self, edges = {}, weights = {}, default = 1):
        self.edges = edges
        self.weights = weights
        self.default = default

    def neighbours(self, node):
        cost = self.weights.get(node, self.default)
        return self.edges[node], cost

class Grid:

    def __init__(self, width, height, walls = []):
        self.width = width
        self.height = height
        self.walls = walls

    def is_in_bounds(self, cell):
        (x, y) = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_solid(self, cell):
        return cell not in self.walls

    def neighbours(self, cell):
        (x, y) = cell
        results = [
            (x + 1, y), # right
            (x, y - 1), # top
            (x - 1, y), # left
            (x, y + 1)  # bottom
        ]
        results = filter(self.is_in_bounds, results)
        results = filter(self.is_solid, results)
        return results

class WeightedGrid(Grid):

    def __init__(self, width, height, walls = [], weights = {}, default = 1):
        super().__init__(width, height, walls)
        self.weights = weights
        self.default = default

    def neighbours(self, cell):
        cost = self.weights.get(cell, self.default)
        return super().neighbours(cell), cost

def reconstruct(self, node_map, start, goal):
    node = goal
    path = []
    while node is not start:
        path.append(node)
        node = node_map[node]
    path.append(start)
    path.reverse()
    return path

def brute_force_search(self, graph, start, goal, width_first = False):
    edges = QStack(width_first)
    edges.put(start)
    node_map = {}
    node_map[start] = None
    while not edges.is_empty:
        node = edges.pop()

        if node is goal:
            break

        for next in graph.neighbours(node):
            if next not in node_map:
                edges.put(next)
                node_map[next] = node
    
    return self.reconstruct(node_map, start, goal)

def manhattan(self, start, goal):
    x1, y1 = start
    x2, y2 = goal
    return abs(x2 - x1) + abs(y2 - y1)

def a_star_search(self, map, start, goal, heuristic):
    
    edges = PriorityQueue()
    came_from = {start: None}
    cost_map = {start: 0}

    while not edges.is_empty:
        node = edges.pop()

        if node is goal:
            return True, self.reconstruct(came_from, start, goal)
        
        for next in node.neighbours():
            next_node, cost = next
            next_cost = cost_map[node] + cost
            if next_node not in cost_map or next_cost < cost_map[next_node]:
                cost_map[next_node] = next_cost
                priority = next_cost + heuristic(goal, next_node)
                edges.put(next_node, priority)
                came_from[next_node] = node

    return False, None

