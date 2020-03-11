from enum import Enum, auto

class MessageTypes(Enum):
    MSG_PATH_DONE       = auto()
    MSG_PATH_FAIL       = auto()
    MSG_UNIT_CREATED    = auto()
    MSG_RESOURCE_NEEDED = auto()
    MSG_RESOURCE_FOUND  = auto()
    MSG_RESOURCE_CHANGE = auto()
    MSG_FETCH_DONE      = auto()
    MSG_BUILDING_NEEDED = auto()
    MSG_BUILDING_DONE   = auto()
    MSG_BUILDING_FINISH = auto()

class Telegram:

    _sender_id = 0
    _receiver_id = 0
    _msg = None
    _data = None

    dispatch_time = 0

    def __init__(self, sender_id: int, receiver_id: tuple, message, data = None):
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._msg = message
        self._data = data

    @property
    def sender_id(self) -> int:
        return self._sender_id

    @property
    def receiver_id(self) -> tuple:
        return self._receiver_id

    @property
    def message(self):
        return self._msg

    @property
    def data(self):
        return self._data