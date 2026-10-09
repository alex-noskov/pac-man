import time
from .parsing import Config
from .models import AppState
from .screens import (GameScreen, MainMenuScreen, InstructionsScreen,
                      HighscoresScreen, ExitScreen, Screen,
                      LevelCompleteScreen, EndScreen)
from .events import Event, EventType
from .graphics import Graphics
from .highscores import HighscoreStore
from collections import deque

FPS = 60
FRAME_TIME = 1 / FPS


class App:
    """Coordinate shared screens and explicit game lifecycle transitions."""

    def __init__(self, config: Config,
                 state: AppState = AppState.MAIN_MENU) -> None:
        """Create graphics, shared highscores, and the initial screen."""
        self.config = config
        self.state = state
        self.graphics = Graphics(
            width=self.config.window_width,
            height=self.config.window_height,
            app_loop=self.app_loop,
        )
        try:
            self._initialize_screens()
        except BaseException:
            self.graphics.quit()
            raise

    def _initialize_screens(self) -> None:
        """Load persistent scores and wire every lifecycle state to a view."""
        self.highscores = HighscoreStore(self.config.highscore_filename)
        self.highscores.load()
        self.game_screen = GameScreen(self.graphics, self.config)
        menu = MainMenuScreen(self.graphics)
        menu.store = self.highscores
        scores = HighscoresScreen(self.graphics)
        scores.store = self.highscores
        self.screens: dict[AppState, Screen] = {
            AppState.GAME: self.game_screen,
            AppState.PAUSE: self.game_screen,
            AppState.ERROR: self.game_screen,
            AppState.GAME_OVER: EndScreen(
                self.graphics, self.highscores, AppState.GAME_OVER),
            AppState.VICTORY: EndScreen(
                self.graphics, self.highscores, AppState.VICTORY),
            AppState.MAIN_MENU: menu,
            AppState.INSTRUCTIONS: InstructionsScreen(self.graphics),
            AppState.HIGHSCORES: scores,
            AppState.LEVEL_COMPLETE: LevelCompleteScreen(self.graphics),
            AppState.EXIT: ExitScreen(),
        }

        self.screen = self.screens[self.state]

    def app_loop(self, event_buffer: deque[Event]) -> None:
        """Drain input, simulate, and render; CLOSE is global."""
        start = time.perf_counter()
        while event_buffer:
            event = event_buffer.popleft()
            next_state = (AppState.EXIT if event.type == EventType.CLOSE
                          else self.screen.handle_event(event))
            if next_state != self.state:
                self._transition_to(next_state)
            if self.state == AppState.EXIT:
                self.graphics.stop_loop()
                return
        next_state = self.screen.update()
        if next_state != self.state:
            self._transition_to(next_state)
        if self.state == AppState.EXIT:
            self.graphics.stop_loop()
            return
        before_sleep = time.perf_counter() - start
        time.sleep(max(0, FRAME_TIME - before_sleep))
        next_state = self.screen.render()
        if next_state != self.state:
            self._transition_to(next_state)
        if self.state == AppState.EXIT:
            self.graphics.stop_loop()

    def _transition_to(self, state: AppState) -> None:
        """Initialize runs, advance levels, and capture terminal scores."""
        previous = self.state
        if hasattr(self, 'game_screen'):
            if state == AppState.GAME and previous == AppState.MAIN_MENU:
                self.game_screen.new_game()
                state = self.game_screen.session.state
            elif (state == AppState.GAME
                  and previous == AppState.LEVEL_COMPLETE):
                self.game_screen.next_level()
                state = self.game_screen.session.state
            if state in (AppState.GAME_OVER, AppState.VICTORY):
                outcome = self.screens[state]
                if isinstance(outcome, EndScreen):
                    outcome.begin(self.game_screen.session.score)
        self.state = state
        self.screen = self.screens[self.state]

    def start(self) -> None:
        """Run the native loop and release resources on every exit path."""
        try:
            self.graphics.start()
        finally:
            self.graphics.quit()
