class Clamped():

    _max = None
    _min = 0
    _current = 0

    def __init__(self, begin = 0, min = None, max = None):
        self._current = begin
        self._min = min
        self._max = max
        self._clamp()

    def _clamp(self):
        if self._max != None and self._current > self._max: self._current = self._max
        elif self._min != None and self._current < self._min: self._current = self._min

    def add(self, step = 1):
        self._current += step
        self._clamp()

    def subtract(self, step = 1):
        self.add(-step)

    def set(self, value):
        self._current = value
        self._clamp()

    def __eq__(self, other):
        return self._current == other
