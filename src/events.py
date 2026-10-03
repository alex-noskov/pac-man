"""Typed input events shared by the native wrapper and screens."""
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """Application actions, independent of native key codes."""

    KEY_LEFT = auto()
    KEY_RIGHT = auto()
    KEY_DOWN = auto()
    KEY_UP = auto()
    KEY_ENTER = auto()
    KEY_ESC = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    CLOSE = auto()
    KEY_PAUSE = auto()
    KEY_CHEAT = auto()
    KEY_INVINCIBLE = auto()
    KEY_SKIP = auto()
    KEY_FREEZE = auto()
    KEY_LIFE = auto()
    KEY_SPEED = auto()
    KEY_POWER = auto()
    KEY_BACKSPACE = auto()
    TEXT = auto()


@dataclass
class Event:
    """One action and its typed payload."""

    type: EventType
    data: dict[str, int | str]


class EventFactory:
    """Construct events without exposing native implementation details."""

    @staticmethod
    def key_left() -> Event:
        """Create the left action."""
        return Event(EventType.KEY_LEFT, {})

    @staticmethod
    def key_right() -> Event:
        """Create the right action."""
        return Event(EventType.KEY_RIGHT, {})

    @staticmethod
    def key_down() -> Event:
        """Create the down action."""
        return Event(EventType.KEY_DOWN, {})

    @staticmethod
    def key_up() -> Event:
        """Create the up action."""
        return Event(EventType.KEY_UP, {})

    @staticmethod
    def key_enter() -> Event:
        """Create the enter action."""
        return Event(EventType.KEY_ENTER, {})

    @staticmethod
    def key_esc() -> Event:
        """Create the esc action."""
        return Event(EventType.KEY_ESC, {})

    @staticmethod
    def key_pause() -> Event:
        """Create the pause action."""
        return Event(EventType.KEY_PAUSE, {})

    @staticmethod
    def key_cheat() -> Event:
        """Create the cheat action."""
        return Event(EventType.KEY_CHEAT, {})

    @staticmethod
    def key_invincible() -> Event:
        """Create the invincible action."""
        return Event(EventType.KEY_INVINCIBLE, {})

    @staticmethod
    def key_skip() -> Event:
        """Create the skip action."""
        return Event(EventType.KEY_SKIP, {})

    @staticmethod
    def key_freeze() -> Event:
        """Create the freeze action."""
        return Event(EventType.KEY_FREEZE, {})

    @staticmethod
    def key_life() -> Event:
        """Create the life action."""
        return Event(EventType.KEY_LIFE, {})

    @staticmethod
    def key_speed() -> Event:
        """Create the speed action."""
        return Event(EventType.KEY_SPEED, {})

    @staticmethod
    def key_power() -> Event:
        """Create the power action."""
        return Event(EventType.KEY_POWER, {})

    @staticmethod
    def key_backspace() -> Event:
        """Create the backspace action."""
        return Event(EventType.KEY_BACKSPACE, {})

    @staticmethod
    def text(text: str) -> Event:
        """Create a text-input event, separate from game controls."""
        return Event(EventType.TEXT, {"text": text})

    @staticmethod
    def mouse_move(x: int, y: int) -> Event:
        """Create a pointer-motion event."""
        return Event(EventType.MOUSE_MOVE, {"x": x, "y": y})

    @staticmethod
    def mouse_down(x: int, y: int, button: int) -> Event:
        """Create a mouse-button event."""
        return Event(EventType.MOUSE_DOWN, {"x": x, "y": y, "button": button})

    @staticmethod
    def close() -> Event:
        """Create a native-window-close event."""
        return Event(EventType.CLOSE, {})
