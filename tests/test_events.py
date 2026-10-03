"""Typed application event factory contracts."""
import unittest

from src.events import EventFactory, EventType


class EventTests(unittest.TestCase):
    def test_control_factories(self) -> None:
        for name in ("left", "right", "up", "down", "enter", "esc",
                     "pause", "cheat", "invincible", "skip", "freeze",
                     "life", "speed", "power", "backspace"):
            with self.subTest(name=name):
                factory = getattr(EventFactory, "key_" + name, None)
                self.assertIsNotNone(factory)
                if factory is not None:
                    event = factory()
                    self.assertEqual(event.type,
                                     getattr(EventType, "KEY_" + name.upper()))
                    self.assertEqual(event.data, {})

    def test_text_factory(self) -> None:
        factory = getattr(EventFactory, "text", None)
        self.assertIsNotNone(factory)
        if factory is not None:
            event = factory("Alex 42")
            self.assertEqual(event.type, EventType.TEXT)
            self.assertEqual(event.data, {"text": "Alex 42"})

    def test_mouse_and_close_factories_preserve_api(self) -> None:
        self.assertEqual(EventFactory.mouse_move(1, 2).data, {"x": 1, "y": 2})
        self.assertEqual(EventFactory.mouse_down(1, 2, 3).data,
                         {"x": 1, "y": 2, "button": 3})
        self.assertEqual(EventFactory.close().type, EventType.CLOSE)
