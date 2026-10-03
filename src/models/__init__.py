from enum import Enum


class AppState(Enum):
    """Represent the current state of the application."""

    MAIN_MENU = "main_menu"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    EXIT = "exit"
    GAME = "game"
    LEVEL_COMPLETE = "level_complete"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    ERROR = "error"


class Directions(Enum):
    """Define grid movement vectors, including the stationary direction."""

    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    STOP = (0, 0)


__all__ = ["AppState", "Directions"]
