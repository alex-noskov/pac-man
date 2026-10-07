"""Integration regressions for actual application lifecycle transitions."""
from collections import deque
from pathlib import Path
import tempfile
import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch

from src.events import EventFactory
from src.models import AppState
from src.app import App
from src.parsing import Config, parse_conf


class LifecycleTests(unittest.TestCase):
    """Use real screens/session with only the graphical boundary replaced."""

    def make_app(self, directory: str) -> App:
        """Construct a live application model without creating native MLX."""
        path = str(Path(directory) / 'scores.json')
        config = Config(window_width=800, window_height=600,
                        highscore_filename=path)
        graphics = MagicMock()
        graphics.get_window_size.return_value = (800, 600)
        with patch('src.app.Graphics', return_value=graphics):
            return App(config)

    def test_menu_start_resets_clock_and_old_run(self) -> None:
        """No menu time or prior score/lives may leak into a new game."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            app = self.make_app(directory)
            game = cast(Any, app.screens[AppState.GAME])
            game.session.score = 999
            game.session.lives = 1
            game._last_update -= 1000
            app._transition_to(AppState.GAME)
            app.app_loop(deque())
            self.assertEqual(app.state, AppState.GAME)
            self.assertEqual(game.session.score, 0)
            self.assertEqual(game.session.lives, app.config.lives)
            self.assertGreater(game.session.time_remaining, 89)

    def test_real_game_over_transition_has_screen_and_name_save(self) -> None:
        """Reproduce the GAME_OVER KeyError through the real app loop."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            app = self.make_app(directory)
            app._transition_to(AppState.GAME)
            game = cast(Any, app.screens[AppState.GAME])
            game.session.time_remaining = 0
            game.session.score = 42
            app.app_loop(deque())
            self.assertEqual(app.state, AppState.GAME_OVER)
            app.app_loop(deque([EventFactory.text('Alex'),
                                EventFactory.key_enter()]))
            self.assertEqual(app.state, AppState.MAIN_MENU)
            saved = Path(app.config.highscore_filename).read_text()
            self.assertIn('Alex', saved)

    def test_final_level_routes_to_victory(self) -> None:
        """The last completion displays victory, not a new maze."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            app = self.make_app(directory)
            app._transition_to(AppState.GAME)
            game = cast(Any, app.screens[AppState.GAME])
            game.session.level_index = len(app.config.levels) - 1
            game.session.skip_level()
            app._transition_to(AppState.LEVEL_COMPLETE)
            app.app_loop(deque([EventFactory.key_enter()]))
            self.assertEqual(app.state, AppState.VICTORY)

    def test_native_close_is_global_on_every_screen(self) -> None:
        """Close works even on screens that do not themselves handle it."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            for state in AppState:
                if state == AppState.EXIT:
                    continue
                app = self.make_app(directory)
                app.state = state
                app.screen = app.screens[state]
                app.app_loop(deque([EventFactory.close()]))
                self.assertEqual(app.state, AppState.EXIT)
                cast(Any, app.graphics).stop_loop.assert_called_once_with()

    def test_supplied_config_preserves_zero_based_level_labels(self) -> None:
        """The checked-in configuration must not discard valid custom mazes."""
        config = parse_conf(Path('config.json'))
        self.assertEqual(len(config.levels), 10)
        self.assertEqual(config.levels[0].width, 14)
        self.assertEqual(config.levels[1].width, 19)
