import pygame
from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..colors import YELLOW, BLACK, TRANSPARENT
from ..ui import Layout


class MainMenuScreen(Screen):
    """Main application menu."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self.layout = Layout()
        self._self_app_state = AppState.MAIN_MENU
        self._backgroung_color = BLACK
        sizes = self.graphics.get_window_size()
        self._width: int = sizes[0]
        self._height: int = sizes[1]
        self._gen_layout()

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

    def _gen_layout(self) -> None:
        self.layout.add_rect(xp=0, yp=15, widthp=20,
                             heightp=10, name="PLAY")
        self.layout.center_rect_x("PLAY")
        self.layout.add_rect(xp=0, yp=30, widthp=20,
                             heightp=10, name="HIGHSCORE")
        self.layout.center_rect_x("HIGHSCORE")
        self.layout.add_rect(xp=0, yp=45, widthp=20,
                             heightp=10, name="INSTRUCTIONS")
        self.layout.center_rect_x("INSTRUCTIONS")
        self.layout.add_rect(xp=0, yp=60, widthp=20,
                             heightp=10, name="EXIT")
        self.layout.center_rect_x("EXIT")

        for rect in self.layout.get_all_rects():
            self.layout.center_rect_x(rect.name)

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.clear(self._backgroung_color)
        for rect in self.layout.get_all_rects():
            absolute = self.layout.get_rect_absolute(
                rect.name, self._width, self._height)
            print(absolute)
            if absolute is None:
                return AppState.EXIT
            self.graphics.draw_rectangle(
                absolute["x"],
                absolute["y"],
                absolute["width"],
                absolute["height"],
                TRANSPARENT
            )
        # self.graphics.draw_text("NADPIS", 100, 100, YELLOW, scale=10)
        self.graphics.refresh()
        return self._self_app_state
