from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    KEY_LEFT = auto()
    KEY_RIGHT = auto()
    KEY_DOWN = auto()
    KEY_UP = auto()
    KEY_ENTER = auto()
    KEY_ESC = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    CLOSE = auto()


@dataclass
class Event:
    type: EventType
    data: dict


class EventFactory:

    @staticmethod
    def key_left():
        return Event(EventType.KEY_LEFT, {})

    @staticmethod
    def key_right():
        return Event(EventType.KEY_RIGHT, {})

    @staticmethod
    def key_down():
        return Event(EventType.KEY_DOWN, {})

    @staticmethod
    def key_up():
        return Event(EventType.KEY_UP, {})

    @staticmethod
    def key_enter():
        return Event(EventType.KEY_ENTER, {})

    @staticmethod
    def key_esc():
        return Event(EventType.KEY_ESC, {})

    @staticmethod
    def mouse_move(x, y):
        return Event(
            EventType.MOUSE_MOVE,
            {"x": x, "y": y}
        )

    @staticmethod
    def mouse_down(x, y, button):
        return Event(
            EventType.MOUSE_DOWN,
            {"x": x, "y": y, "button": button}
        )

    @staticmethod
    def close():
        return Event(EventType.CLOSE, {})
