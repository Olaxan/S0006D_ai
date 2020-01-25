class Clamped:

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

    def add(self, step: int):
        self._current += step
        self._clamp()

    def sub(self, step: int):
        self.add(-step)

    def set(self, value: int):
        self._current = value
        self._clamp()

    @property
    def is_max(self):
        return self._current == self._max

    @property
    def is_min(self):
        return self._current == self._min

    @property
    def current(self):
        return self._current

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, max):
        self._max = max

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, min):
        self._min = min

    
