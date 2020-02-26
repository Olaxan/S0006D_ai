from enum import Enum, auto

class MessageTypes(Enum):
    MSG_MEETING             = auto()    # Meeting invitation, data is shared MeetingState
    MSG_MEETING_REPLY       = auto()    # Reply to meeting invitation, data is True/False for Accept/Decline
    MSG_MEETING_CANCEL      = auto()    # Message to cancel planned meeting
    MSG_MEETING_LEAVING     = auto()    # Message to announce leaving a meeting
    MSG_WAKEUP              = auto()    # Message to wake up during sleep state
    MSG_ARRIVAL             = auto()    # Message to announce arriving at a new location, data is location string
    MSG_PATH_FAIL           = auto()    # Message to announce agent failed to path to location

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