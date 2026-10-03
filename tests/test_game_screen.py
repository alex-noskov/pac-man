"""Headless regression tests for gameplay UI orchestration."""
import unittest
from typing import Any, cast
from unittest.mock import MagicMock

from src.events import EventFactory
from src.models import AppState, Directions
from src.parsing import Config
from src.screens.game_screen import GameScreen


class GameScreenTests(unittest.TestCase):
    """Exercise input and monotonic timing without opening a window."""

    def make_screen(self) -> tuple[GameScreen, Any, list[float]]:
        """Return a screen backed by a controlled session and clock."""
        graphics = MagicMock()
        graphics.get_window_size.return_value = (800, 600)
        session = MagicMock(state=AppState.GAME)
        now = [10.0]
        screen = GameScreen(cast(Any, graphics), Config(),
                            session=session, clock=lambda: now[0])
        return screen, session, now

    def test_arrows_queue_direction_without_advancing_simulation(self) -> None:
        """Events queue turns rather than prematurely moving grid cells."""
        screen, session, _ = self.make_screen()
        self.assertEqual(screen.handle_event(EventFactory.key_up()),
                         AppState.GAME)
        session.set_direction.assert_called_once_with(Directions.UP)
        session.update.assert_not_called()

    def test_escape_pauses_instead_of_abandoning_game(self) -> None:
        """Escape preserves the game through the pause menu."""
        screen, session, _ = self.make_screen()
        session.toggle_pause.side_effect = lambda: setattr(
            session, 'state', AppState.PAUSE)
        self.assertEqual(screen.handle_event(EventFactory.key_esc()),
                         AppState.PAUSE)
        session.toggle_pause.assert_called_once_with()

    def test_elapsed_time_drives_update(self) -> None:
        """Movement and timers use elapsed time, not a count of frames."""
        screen, session, now = self.make_screen()
        now[0] += 0.125
        screen.update()
        session.update.assert_called_once_with(0.125)

    def test_resume_resets_clock_so_pause_is_not_charged(self) -> None:
        """Time spent paused cannot leak into the first resumed frame."""
        screen, session, now = self.make_screen()
        session.state = AppState.PAUSE
        now[0] += 60
        session.toggle_pause.side_effect = lambda: setattr(
            session, 'state', AppState.GAME)
        screen.handle_event(EventFactory.key_enter())
        now[0] += 0.1
        screen.update()
        self.assertAlmostEqual(session.update.call_args.args[0], 0.1)

    def test_pause_return_to_menu_does_not_resume(self) -> None:
        """Pause offers a separate return-to-menu selection."""
        screen, session, _ = self.make_screen()
        session.state = AppState.PAUSE
        screen.handle_event(EventFactory.key_down())
        self.assertEqual(screen.handle_event(EventFactory.key_enter()),
                         AppState.MAIN_MENU)
        session.toggle_pause.assert_not_called()

    def test_turning_cheat_mode_off_clears_ongoing_advantages(self) -> None:
        """Normal play cannot silently retain hidden cheat modifiers."""
        screen, session, _ = self.make_screen()
        session.cheat_enabled = True
        session.invincible = True
        session.ghosts_frozen = True
        session.speed_multiplier = 2.0
        screen.handle_event(EventFactory.key_cheat())
        self.assertFalse(session.cheat_enabled)
        self.assertFalse(session.invincible)
        self.assertFalse(session.ghosts_frozen)
        self.assertEqual(session.speed_multiplier, 1.0)
