from enum import Enum


class AppState(Enum):
    """Represent the current state of the application."""

    MAIN_MENU = "main_menu"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    EXIT = "exit"
    GAME = "game"
    # PAUSE = "pause"
    # GAME_OVER = "game_over"
    # VICTORY = "victory"


class Directions(Enum):
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    STOP = (0, 0)


__all__ = ["AppState", "Directions"]
