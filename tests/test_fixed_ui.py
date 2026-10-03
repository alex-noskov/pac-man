"""Fixed laptop-window dimensions and readable bitmap font regressions."""
import unittest
from typing import Any, cast
from unittest.mock import MagicMock

from src import ui
from src.colors import BLACK
from src.highscores import HighscoreStore
from src.models import AppState
from src.parsing import Config, parse
from src.screens import (EndScreen, GameScreen, HighscoresScreen,
                         InstructionsScreen, LevelCompleteScreen,
                         MainMenuScreen)


class FixedUiTests(unittest.TestCase):
    """UI sizes are simple constants rather than automatic font fitting."""

    def test_level_complete_title_contrasts_with_yellow_panel(self) -> None:
        """Yellow panels need dark lettering for readable confirmation."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (1024, 640)
        screen = LevelCompleteScreen(cast(Any, graphics))
        screen.render()
        title = next(c for c in graphics.draw_text.call_args_list
                     if c.kwargs.get('text') == 'LEVEL COMPLETE!')
        self.assertEqual(title.kwargs['color'], BLACK)

    def test_default_and_supplied_window_fit_a_laptop(self) -> None:
        """The shipped and fallback windows use the same modest dimensions."""
        for config in (Config(), parse('config.json')):
            self.assertEqual((config.window_width, config.window_height),
                             (1024, 640))

    def test_named_font_constants_have_fixed_sizes(self) -> None:
        """Font magnification is explicit and easy to adjust for evaluation."""
        for name, value in (('NORMAL_TEXT_SCALE', 2),
                            ('TITLE_TEXT_SCALE', 3), ('HUD_TEXT_SCALE', 2)):
            self.assertEqual(getattr(ui, name, None), value)

    def test_all_screens_keep_text_and_elements_inside_laptop_window(
            self) -> None:
        """All menus, full highscore table, outcomes and HUD fit 1024x640."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (1024, 640)
        g = cast(Any, graphics)
        store = HighscoreStore('unused.json')
        for i in range(10):
            store.add(f'PLAYER{i}', 999999)
        menu = MainMenuScreen(g)
        menu.store = store
        scores = HighscoresScreen(g)
        scores.store = store
        game = GameScreen(g, Config())
        game.session.score = 999999
        game.session.cheat_enabled = True
        game.session.ghosts_frozen = True
        screens = [menu, scores, InstructionsScreen(g),
                   LevelCompleteScreen(g), game]
        for state in (AppState.GAME_OVER, AppState.VICTORY):
            outcome = EndScreen(g, store, state)
            outcome.begin(999999)
            outcome.name = 'PLAYER1234'
            screens.append(outcome)
        for screen in screens:
            graphics.reset_mock()
            screen.render()
            for call in graphics.draw_text.call_args_list:
                text = call.kwargs.get('text', call.args[0]
                                       if call.args else '')
                x = call.kwargs.get('x', call.args[1]
                                    if len(call.args) > 1 else 0)
                y = call.kwargs.get('y', call.args[2]
                                    if len(call.args) > 2 else 0)
                scale = call.kwargs.get('scale', 1)
                spacing = call.kwargs.get('spacing', 1)
                with self.subTest(screen=type(screen).__name__, text=text):
                    self.assertIn(scale, (2, 3))
                    length = len(text) * 5 * scale
                    length += max(0, len(text) - 1) * spacing
                    self.assertGreaterEqual(x, 0)
                    self.assertGreaterEqual(y, 0)
                    self.assertLessEqual(x + length, 1024)
                    self.assertLessEqual(y + 8 * scale, 640)

    def test_name_field_uses_same_font_in_different_window_sizes(self) -> None:
        """Window dimensions and name length cannot alter the font size."""
        scales = []
        for size in ((1024, 640), (1200, 800)):
            graphics = MagicMock()
            graphics.get_window_size.return_value = size
            screen = EndScreen(cast(Any, graphics),
                               HighscoreStore('unused.json'), AppState.VICTORY)
            for name in ('', 'A', 'PLAYER1234'):
                screen.name = name
                graphics.reset_mock()
                screen.render()
                text = name or 'TYPE YOUR NAME HERE'
                call = next(c for c in graphics.draw_text.call_args_list
                            if c.args[0] == text)
                scales.append(call.kwargs['scale'])
        self.assertEqual(scales, [2] * 6)
