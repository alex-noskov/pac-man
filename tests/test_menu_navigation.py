"""Regression coverage for the ordinary fixed main-menu choices."""
import unittest
from typing import Any, cast
from unittest.mock import MagicMock

from src.ui.events import EventFactory
from src.models import AppState
from src.ui.screen_main_menu import MainMenuScreen


class MenuNavigationTests(unittest.TestCase):
    """Keep button order and wrap keyboard navigation."""

    def test_buttons_keep_their_order_and_wrap_at_both_ends(self) -> None:
        """Up from Play wraps to Exit and Down from Exit wraps to Play."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (1024, 640)
        menu = MainMenuScreen(cast(Any, graphics))

        menu.handle_event(EventFactory.key_up())
        self.assertEqual(
            menu.handle_event(EventFactory.key_enter()),
            AppState.EXIT,
        )

        menu.handle_event(EventFactory.key_down())
        self.assertEqual(
            menu.handle_event(EventFactory.key_enter()),
            AppState.GAME,
        )

        for state in (
            AppState.HIGHSCORES,
            AppState.INSTRUCTIONS,
            AppState.EXIT,
            AppState.GAME,
        ):
            menu.handle_event(EventFactory.key_down())
            self.assertEqual(
                menu.handle_event(EventFactory.key_enter()),
                state,
            )

        self.assertEqual(
            menu.layout.get_rect_names(),
            [
                'GAME',
                'HIGHSCORES',
                'INSTRUCTIONS',
                'EXIT',
                'CONTROL_INFO',
            ],
        )
