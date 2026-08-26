import sys
# import time
from src.parsing import parse, Config
from .models import AppState
from .screens import (GameScreen, MainMenuScreen, InstructionsScreen,
                      HighscoresScreen, ExitScreen, Screen)
# from .events import EventType
from .graphics import Graphics
from collections import deque

FPS = 60
FRAME_TIME = 1 / FPS


class PacMan:
    def __init__(self, config: Config, state: AppState = AppState.MAIN_MENU
                 ) -> None:
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
        # print("APP LOOP")
        # start = time.perf_counter()
        while event_buffer:
            # for _ in range(min(100, len(event_buffer))):
            event = event_buffer.popleft()
            next_state = self.screen.handle_event(event)
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
        # elapsed = time.perf_counter() - start
        # time.sleep(max(0, FRAME_TIME - elapsed))
        # print(self.graphics.get_mouse_position())
        self.screen.render()

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
    pac_man = PacMan(config, AppState.GAME)
    pac_man.start()
