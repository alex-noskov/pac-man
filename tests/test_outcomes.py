"""Terminal outcome screen contracts and persistent name entry."""
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

from src.events import EventFactory
from src.highscores import HighscoreStore
from src.models import AppState
from src.screens import EndScreen


class OutcomeTests(unittest.TestCase):
    """Win and loss must both save a valid score and return to the menu."""

    def test_both_outcomes_show_visible_keyboard_input_and_save_prompt(
            self) -> None:
        """An empty name must look like a field, not invisible blank text."""
        for state in (AppState.GAME_OVER, AppState.VICTORY):
            graphics = MagicMock()
            graphics.get_window_size.return_value = (800, 600)
            screen = EndScreen(cast(Any, graphics),
                               HighscoreStore('unused.json'), state)
            screen.begin(42)
            screen.render()
            texts = [str(c.args[0]) for c in
                     graphics.draw_text.call_args_list]
            self.assertTrue(any('TYPE ON YOUR KEYBOARD' in t for t in texts))
            self.assertIn('TYPE YOUR NAME HERE', texts)
            self.assertTrue(any('ENTER TO SAVE' in t for t in texts))
            self.assertGreaterEqual(graphics.draw_rectangle.call_count, 2)
            graphics.reset_mock()
            screen.handle_event(EventFactory.text('PLAYER42'))
            screen.render()
            texts = [str(c.args[0]) for c in
                     graphics.draw_text.call_args_list]
            self.assertIn('PLAYER42', texts)
            self.assertNotIn('TYPE YOUR NAME HERE', texts)

    def test_input_and_buttons_fit_small_supported_windows(self) -> None:
        """Name input and confirmation remain inside a 320x240 window."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (320, 240)
        screen = EndScreen(cast(Any, graphics),
                           HighscoreStore('unused.json'), AppState.GAME_OVER)
        screen.render()
        for call in graphics.draw_text.call_args_list:
            text, x, y = call.args[:3]
            scale = call.kwargs.get('scale', 1)
            spacing = call.kwargs.get('spacing', 1)
            text_width = len(text) * 5 * scale + (len(text) - 1) * spacing
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x + text_width, 320)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y + 8 * scale, 240)

    def test_win_and_loss_support_name_input_save_and_return(self) -> None:
        """Enter saves the displayed final score for either outcome."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            store = HighscoreStore(Path(directory) / 'scores.json')
            graphics = cast(Any, MagicMock())
            for state in (AppState.GAME_OVER, AppState.VICTORY):
                screen = EndScreen(graphics, store, state)
                screen.begin(123)
                screen.handle_event(EventFactory.text('Player 42'))
                self.assertEqual(screen.handle_event(EventFactory.key_enter()),
                                 AppState.MAIN_MENU)
                loaded = HighscoreStore(store.path)
                loaded.load()
                self.assertEqual(loaded.entries[0],
                                 {'name': 'Player 42', 'score': 123})

    def test_name_filter_length_backspace_and_empty_default(self) -> None:
        """Editing enforces the same name rules as persistent storage."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            store = HighscoreStore(Path(directory) / 'scores.json')
            screen = EndScreen(cast(Any, MagicMock()), store,
                               AppState.GAME_OVER)
            screen.begin(0)
            screen.handle_event(EventFactory.text('ABC!def1234567é'))
            self.assertEqual(screen.name, 'ABCdef1234')
            screen.handle_event(EventFactory.key_backspace())
            self.assertEqual(screen.name, 'ABCdef123')
            screen.begin(0)
            screen.handle_event(EventFactory.key_enter())
            self.assertEqual(store.entries[0]['name'], 'PLAYER')

    def test_failed_save_stays_on_outcome_and_retry_is_not_duplicated(
            self) -> None:
        """An unwritable path is recoverable and retries do not duplicate."""
        with tempfile.TemporaryDirectory(dir='.') as directory:
            root = Path(directory)
            store = HighscoreStore(root / 'missing' / 'scores.json')
            screen = EndScreen(cast(Any, MagicMock()), store,
                               AppState.VICTORY)
            screen.begin(42)
            screen.handle_event(EventFactory.text('A'))
            self.assertEqual(screen.handle_event(EventFactory.key_enter()),
                             AppState.VICTORY)
            self.assertTrue(screen.message)
            store.path = root / 'scores.json'
            self.assertEqual(screen.handle_event(EventFactory.key_enter()),
                             AppState.MAIN_MENU)
            self.assertEqual(len(store.entries), 1)
