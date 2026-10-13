"""Menu data display contracts exercised at the graphics boundary."""
import unittest
from typing import Any, cast
from unittest.mock import MagicMock

from src.highscores import HighscoreStore
from src.ui.screen_highscores import HighscoresScreen
from src.ui.screen_main_menu import MainMenuScreen


class ScoreDisplayTests(unittest.TestCase):
    """Both the main menu and score view must show names and scores."""

    def test_both_menus_render_persistent_scores(self) -> None:
        """A loaded name and score cannot remain hidden behind a title."""
        for screen_class in (HighscoresScreen, MainMenuScreen):
            graphics = MagicMock()
            graphics.get_window_size.return_value = (800, 600)
            screen = screen_class(cast(Any, graphics))
            store = HighscoreStore('unused.json')
            store.add('TESTER', 123)
            screen.store = store
            screen.render()
            texts = [str(c.kwargs.get('text', c.args[0] if c.args else ''))
                     for c in graphics.draw_text.call_args_list]
            self.assertTrue(any('TESTER' in text and '123' in text
                                for text in texts), texts)
