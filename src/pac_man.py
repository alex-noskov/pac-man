import sys
# import time
from src.parsing import parse, Config
from .models import AppState
from .screens import (MainMenuScreen, InstructionsScreen,
                      HighscoresScreen, ExitScreen, Screen)
# from .graphics import Graphics
from .graphics import Graphics
# FPS = 60
# FRAME_TIME = 1 / FPS


class PacMan:
    def __init__(self, config: Config, state: AppState = AppState.MAIN_MENU
                 ) -> None:
        self.config = config
        self.state = state
        self.graphics = Graphics(
            width=self.config.window_width,
            height=self.config.window_height,
            app_loop=self.app_loop)
        self.screens: dict[AppState, Screen] = {
            AppState.MAIN_MENU: MainMenuScreen(self.graphics),
            AppState.INSTRUCTIONS: InstructionsScreen(self.graphics),
            AppState.HIGHSCORES: HighscoresScreen(self.graphics),
            AppState.EXIT: ExitScreen()
        }

    def app_loop(self) -> None:
        print("APP LOOP")

    def _transition_to(self, state: AppState) -> None:
        print(f"NEW STATE: {self.state} -> {state}")
        self.state = state

    def start(self) -> None:
        print("Pac Man application started!")
        try:
            self.graphics.start()
        finally:
            self.graphics.quit()
        # while True:
        #    # start = time.perf_counter()
        #    screen = self.screens[self.state]
        #    next_state = self.state
        #    for event in self.graphics.get_events():
        #        next_state = screen.handle_event(event)
        #        if next_state != self.state:
        #            self._transition_to(next_state)
        #        if next_state == AppState.EXIT:
        #            break
        #    if next_state == AppState.EXIT:
        #        break
        #    next_state = screen.update()
        #    if next_state != self.state:
        #        self._transition_to(next_state)
        #    if next_state == AppState.EXIT:
        #        break
        #    # elapsed = time.perf_counter() - start
        #    # time.sleep(max(0, FRAME_TIME - elapsed))
        #    # time.sleep(0)
        #    screen.render()
        # self.graphics.quit()


def main() -> None:
    """Start the Pac-Man game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        return
    config = parse(sys.argv[1])
    pac_man = PacMan(config)
    pac_man.start()
