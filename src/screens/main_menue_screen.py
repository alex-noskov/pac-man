import pygame
from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..colors import YELLOW, BLACK


class MainMenuScreen(Screen):
    """Main application menu."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self._self_app_state = AppState.MAIN_MENU
        self._backgroung_color = BLACK

    def handle_event(self, event) -> AppState:
        """Handle an input event."""
        if event is not None:
            if event.type == pygame.QUIT:
                print(event)
                return AppState.EXIT
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.clear(self._backgroung_color)
        self.graphics.draw_text("welcum", 100, 100, YELLOW, scale=10)
        self.graphics.refresh()
        return self._self_app_state
