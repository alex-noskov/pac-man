from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    KEY_DOWN = auto()
    KEY_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    CLOSE = auto()


@dataclass
class Event:
    type: EventType
    data: dict


class EventFactory:

    @staticmethod
    def key_down(key):
        return Event(
            EventType.KEY_DOWN,
            {"key": key}
        )

    @staticmethod
    def key_up(key):
        return Event(
            EventType.KEY_UP,
            {"key": key}
        )

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
