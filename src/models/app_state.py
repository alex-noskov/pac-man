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
