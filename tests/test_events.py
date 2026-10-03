"""Typed application event factory contracts."""
import unittest

from src.events import EventFactory, EventType


class EventTests(unittest.TestCase):
    def test_control_factories(self) -> None:
        cases = [
            (EventFactory.key_left, EventType.KEY_LEFT),
            (EventFactory.key_right, EventType.KEY_RIGHT),
            (EventFactory.key_up, EventType.KEY_UP),
            (EventFactory.key_down, EventType.KEY_DOWN),
            (EventFactory.key_enter, EventType.KEY_ENTER),
            (EventFactory.key_esc, EventType.KEY_ESC),
            (EventFactory.key_pause, EventType.KEY_PAUSE),
            (EventFactory.key_cheat, EventType.KEY_CHEAT),
            (EventFactory.key_invincible, EventType.KEY_INVINCIBLE),
            (EventFactory.key_skip, EventType.KEY_SKIP),
            (EventFactory.key_freeze, EventType.KEY_FREEZE),
            (EventFactory.key_life, EventType.KEY_LIFE),
            (EventFactory.key_speed, EventType.KEY_SPEED),
            (EventFactory.key_power, EventType.KEY_POWER),
            (EventFactory.key_backspace, EventType.KEY_BACKSPACE),
        ]
        for factory, expected_type in cases:
            with self.subTest(type=expected_type):
                event = factory()
                self.assertEqual(event.type, expected_type)
                self.assertEqual(event.data, {})

    def test_text_factory(self) -> None:
        event = EventFactory.text("Alex 42")
        self.assertEqual(event.type, EventType.TEXT)
        self.assertEqual(event.data, {"text": "Alex 42"})

    def test_mouse_and_close_factories_preserve_api(self) -> None:
        self.assertEqual(EventFactory.mouse_move(1, 2).data, {"x": 1, "y": 2})
        self.assertEqual(EventFactory.mouse_down(1, 2, 3).data,
                         {"x": 1, "y": 2, "button": 3})
        self.assertEqual(EventFactory.close().type, EventType.CLOSE)
