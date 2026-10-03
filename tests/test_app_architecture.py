from collections import deque
from contextlib import redirect_stdout
from io import StringIO
import unittest
from typing import Any, cast
from unittest.mock import MagicMock, call, patch

from src.events import EventFactory
from src.models import AppState
from src.pac_man import App, main


class RecordingScreen:
    """Small screen double that records orchestration calls."""

    def __init__(
        self,
        name: str,
        timeline: list[tuple],
        *,
        event_states: list[AppState] | None = None,
        update_state: AppState,
        render_state: AppState,
    ) -> None:
        self.name = name
        self.timeline = timeline
        self.event_states = deque(event_states or [])
        self.update_state = update_state
        self.render_state = render_state

    def handle_event(self, event: object) -> AppState:
        self.timeline.append((self.name, "handle_event", event))
        if self.event_states:
            return self.event_states.popleft()
        return self.update_state

    def update(self) -> AppState:
        self.timeline.append((self.name, "update"))
        return self.update_state

    def render(self) -> AppState:
        self.timeline.append((self.name, "render"))
        return self.render_state


class MainEntryPointTests(unittest.TestCase):
    def test_main_without_exactly_one_argument_prints_usage(self) -> None:
        output = StringIO()

        with (
            patch("src.pac_man.sys.argv", ["pac-man"]),
            patch("src.pac_man.parse") as parse_mock,
            patch("src.pac_man.App") as app_class,
            redirect_stdout(output),
        ):
            main()

        self.assertIn(
            "Usage: python3 pac-man.py <config.json>",
            output.getvalue(),
        )
        parse_mock.assert_not_called()
        app_class.assert_not_called()

    def test_main_parses_config_builds_app_and_starts_it(self) -> None:
        config = object()
        app = MagicMock()

        with (
            patch("src.pac_man.sys.argv", ["pac-man", "settings.json"]),
            patch("src.pac_man.parse", return_value=config) as parse_mock,
            patch("src.pac_man.App", return_value=app) as app_class,
            patch("builtins.print"),
        ):
            main()

        parse_mock.assert_called_once_with("settings.json")
        app_class.assert_called_once_with(config, AppState.MAIN_MENU)
        app.start.assert_called_once_with()


class AppConstructionTests(unittest.TestCase):
    def test_constructor_shares_graphics_between_screens(self) -> None:
        config = MagicMock(window_width=800, window_height=600)
        graphics = object()
        game_screen = object()
        main_menu = object()
        instructions = object()
        highscores = object()
        level_complete = object()
        exit_screen = object()

        with (
            patch(
                "src.pac_man.Graphics",
                return_value=graphics,
            ) as graphics_class,
            patch(
                "src.pac_man.GameScreen",
                return_value=game_screen,
            ) as game_class,
            patch(
                "src.pac_man.MainMenuScreen",
                return_value=main_menu,
            ) as menu_class,
            patch(
                "src.pac_man.InstructionsScreen",
                return_value=instructions,
            ) as instructions_class,
            patch(
                "src.pac_man.HighscoresScreen",
                return_value=highscores,
            ) as highscores_class,
            patch(
                "src.pac_man.LevelCompleteScreen",
                return_value=level_complete,
            ) as level_complete_class,
            patch(
                "src.pac_man.ExitScreen",
                return_value=exit_screen,
            ) as exit_class,
        ):
            app = App(config)

        graphics_class.assert_called_once_with(
            width=800,
            height=600,
            app_loop=app.app_loop,
        )
        game_class.assert_called_once_with(graphics, config)
        menu_class.assert_called_once_with(graphics)
        instructions_class.assert_called_once_with(graphics)
        highscores_class.assert_called_once_with(graphics)
        level_complete_class.assert_called_once_with(graphics)
        exit_class.assert_called_once_with()
        self.assertEqual(app.state, AppState.MAIN_MENU)
        self.assertIs(app.screen, main_menu)
        self.assertEqual(
            set(app.screens),
            {
                AppState.GAME,
                AppState.MAIN_MENU,
                AppState.INSTRUCTIONS,
                AppState.HIGHSCORES,
                AppState.LEVEL_COMPLETE,
                AppState.EXIT,
            },
        )


class AppLoopTests(unittest.TestCase):
    def make_app(
        self,
        state: AppState,
        screens: dict[AppState, RecordingScreen],
    ) -> App:
        app = App.__new__(App)
        app.state = state
        app.screens = cast(Any, screens)
        app.screen = cast(Any, screens[state])
        app.graphics = cast(Any, MagicMock())
        return app

    def test_new_screen_handles_events_after_transition(self) -> None:
        timeline: list[tuple] = []
        first_event = EventFactory.key_enter()
        second_event = EventFactory.key_right()
        menu = RecordingScreen(
            "menu",
            timeline,
            event_states=[AppState.GAME],
            update_state=AppState.MAIN_MENU,
            render_state=AppState.MAIN_MENU,
        )
        game = RecordingScreen(
            "game",
            timeline,
            event_states=[AppState.GAME],
            update_state=AppState.GAME,
            render_state=AppState.GAME,
        )
        app = self.make_app(
            AppState.MAIN_MENU,
            {AppState.MAIN_MENU: menu, AppState.GAME: game},
        )

        with patch("src.pac_man.time.sleep"), patch("builtins.print"):
            app.app_loop(deque([first_event, second_event]))

        self.assertEqual(
            timeline,
            [
                ("menu", "handle_event", first_event),
                ("game", "handle_event", second_event),
                ("game", "update"),
                ("game", "render"),
            ],
        )
        self.assertEqual(app.state, AppState.GAME)

    def test_update_transition_changes_which_screen_is_rendered(self) -> None:
        timeline: list[tuple] = []
        game = RecordingScreen(
            "game",
            timeline,
            update_state=AppState.LEVEL_COMPLETE,
            render_state=AppState.GAME,
        )
        completed = RecordingScreen(
            "level_complete",
            timeline,
            update_state=AppState.LEVEL_COMPLETE,
            render_state=AppState.LEVEL_COMPLETE,
        )
        app = self.make_app(
            AppState.GAME,
            {
                AppState.GAME: game,
                AppState.LEVEL_COMPLETE: completed,
            },
        )

        with patch("src.pac_man.time.sleep"), patch("builtins.print"):
            app.app_loop(deque())

        self.assertEqual(
            timeline,
            [
                ("game", "update"),
                ("level_complete", "render"),
            ],
        )
        self.assertEqual(app.state, AppState.LEVEL_COMPLETE)

    def test_exit_event_stops_loop_before_update_or_render(self) -> None:
        timeline: list[tuple] = []
        close_event = EventFactory.close()
        menu = RecordingScreen(
            "menu",
            timeline,
            event_states=[AppState.EXIT],
            update_state=AppState.MAIN_MENU,
            render_state=AppState.MAIN_MENU,
        )
        exit_screen = RecordingScreen(
            "exit",
            timeline,
            update_state=AppState.EXIT,
            render_state=AppState.EXIT,
        )
        app = self.make_app(
            AppState.MAIN_MENU,
            {AppState.MAIN_MENU: menu, AppState.EXIT: exit_screen},
        )

        with patch("src.pac_man.time.sleep"), patch("builtins.print"):
            app.app_loop(deque([close_event]))

        self.assertEqual(timeline, [("menu", "handle_event", close_event)])
        self.assertEqual(app.state, AppState.EXIT)
        cast(MagicMock, app.graphics.stop_loop).assert_called_once_with()

    def test_start_runs_the_native_loop_then_releases_graphics(self) -> None:
        app = App.__new__(App)
        graphics = MagicMock()
        graphics.attach_mock(MagicMock(), "start")
        graphics.attach_mock(MagicMock(), "quit")
        app.graphics = cast(Any, graphics)

        app.start()

        self.assertEqual(
            graphics.mock_calls,
            [call.start(), call.quit()],
        )

    def test_render_requested_transition_is_applied(self) -> None:
        """Apply transitions consistently, including render results."""
        timeline: list[tuple] = []
        menu = RecordingScreen(
            "menu",
            timeline,
            update_state=AppState.MAIN_MENU,
            render_state=AppState.GAME,
        )
        game = RecordingScreen(
            "game",
            timeline,
            update_state=AppState.GAME,
            render_state=AppState.GAME,
        )
        app = self.make_app(
            AppState.MAIN_MENU,
            {AppState.MAIN_MENU: menu, AppState.GAME: game},
        )

        with patch("src.pac_man.time.sleep"), patch("builtins.print"):
            app.app_loop(deque())

        self.assertEqual(app.state, AppState.GAME)


class ResourceFailureTests(unittest.TestCase):
    def test_start_releases_graphics_when_loop_fails(self) -> None:
        """Native resources must be released even on a loop failure."""
        app = App.__new__(App)
        graphics = MagicMock()
        graphics.start.side_effect = RuntimeError("loop failed")
        app.graphics = cast(Any, graphics)
        with self.assertRaises(RuntimeError):
            app.start()
        graphics.quit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
