from .screen import Screen
from ..models import AppState
from ..graphics import Graphics


class HighscoresScreen(Screen):
    """Highscores."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self.self_app_state = AppState.HIGHSCORES

    def handle_event(self, event) -> AppState:
        """Handle an input event."""
        return self.self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self.self_app_state

    def render(self) -> AppState:
        """Render the screen."""
        print("HighscoresScreen render!")
        return self.self_app_state
