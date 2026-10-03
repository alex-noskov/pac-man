"""Regression coverage for the ordinary fixed main-menu choices."""
import unittest
from typing import Any, cast
from unittest.mock import MagicMock

from src.events import EventFactory
from src.models import AppState
from src.screens import MainMenuScreen


class MenuNavigationTests(unittest.TestCase):
    """Keep the original order and non-wrapping keyboard behavior."""

    def test_buttons_keep_their_order_and_clamp_at_both_ends(self) -> None:
        """Repeated Up/Down cannot go past Play/Exit or change destinations."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (1024, 640)
        menu = MainMenuScreen(cast(Any, graphics))
        for _ in range(3):
            menu.handle_event(EventFactory.key_up())
        self.assertEqual(menu.handle_event(EventFactory.key_enter()),
                         AppState.GAME)
        for state in (AppState.HIGHSCORES, AppState.INSTRUCTIONS,
                      AppState.EXIT):
            menu.handle_event(EventFactory.key_down())
            result = menu.handle_event(EventFactory.key_enter())
            self.assertEqual(result, state)
        for _ in range(3):
            menu.handle_event(EventFactory.key_down())
        self.assertEqual(menu.handle_event(EventFactory.key_enter()),
                         AppState.EXIT)
        self.assertEqual(menu.layout.get_rect_names(),
                         ['GAME', 'HIGHSCORES', 'INSTRUCTIONS', 'EXIT',
                          'CONTROL_INFO'])
