import sys
import time
from src.parsing import parse, Config
from .models import AppState
from .screens import (GameScreen, MainMenuScreen, InstructionsScreen,
                      HighscoresScreen, ExitScreen, Screen)
# from .events import EventType
from .graphics import Graphics
from collections import deque

FPS = 120
FRAME_TIME = 1 / FPS


class App:
    def __init__(self, config: Config,
                 state: AppState = AppState.MAIN_MENU) -> None:
        self.config = config
        self.state = state
        self.graphics = Graphics(
            width=self.config.window_width,
            height=self.config.window_height,
            app_loop=self.app_loop,
        )
        self.screens: dict[AppState, Screen] = {
            AppState.GAME: GameScreen(self.graphics, self.config),
            AppState.MAIN_MENU: MainMenuScreen(self.graphics),
            AppState.INSTRUCTIONS: InstructionsScreen(self.graphics),
            AppState.HIGHSCORES: HighscoresScreen(self.graphics),
            AppState.EXIT: ExitScreen()
        }
        self.screen = self.screens[self.state]

        # self.x = 0
        # self.y = 0

    def app_loop(self, event_buffer: deque) -> None:
        start = time.perf_counter()
        event_start = time.perf_counter()
        while event_buffer:
            event = event_buffer.popleft()
            next_state = self.screen.handle_event(event)
            if next_state != self.state:
                self._transition_to(next_state)
            if self.state == AppState.EXIT:
                self.graphics.stop_loop()
                return
        event_time = time.perf_counter() - event_start

        update_start = time.perf_counter()
        next_state = self.screen.update()
        if next_state != self.state:
            self._transition_to(next_state)
        update_time = time.perf_counter() - update_start

        before_sleep = time.perf_counter() - start
        time.sleep(max(0, FRAME_TIME - before_sleep))

        render_start = time.perf_counter()
        self.screen.render()
        render_time = time.perf_counter() - render_start

        total = time.perf_counter() - start

        # print(
        #    f"events={event_time*1000:.1f}ms "
        #    f"update={update_time*1000:.1f}ms "
        #    f"render={render_time*1000:.1f}ms "
        #    f"total={total*1000:.1f}ms"
        # )

    def _transition_to(self, state: AppState) -> None:
        print(f"NEW STATE: {self.state} -> {state}")
        self.state = state
        self.screen = self.screens[self.state]

    def start(self) -> None:
        self.graphics.start()
        self.graphics.quit()


def main() -> None:
    """Start the Pac-Man game."""
    print("Pac Man application started!")
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        return
    config = parse(sys.argv[1])
    app = App(config, AppState.GAME)
    app.start()
