import pygame
from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..colors import YELLOW, BLACK, GREEN, WHITE
from ..ui import Layout, AbsoluteRect


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
        self._cache: dict[str, AbsoluteRect] = {}
        self._gen_layout()
        self._cache_abs_layout()

    def handle_event(self, event: pygame.event.Event) -> AppState:
        """Handle an input event."""
        if event is not None:
            if event.type == pygame.QUIT:
                print(event)
                return AppState.EXIT
            if event.type == pygame.MOUSEMOTION:
                if event.pos is not None:
                    if self._cache["PLAY"].contains(event.pos[0],
                                                    event.pos[1]):
                        self._cache["PLAY"].color = GREEN
                        self._cache["PLAY_TEXT"].color = GREEN
                        if self._cache["PLAY_TEXT"].text is not None:
                            self._cache["PLAY_TEXT"].text.color = WHITE
                    elif self._cache["HIGHSCORE"].contains(event.pos[0],
                                                           event.pos[1]):
                        self._cache["HIGHSCORE"].color = GREEN
                        self._cache["HIGHSCORE_TEXT"].color = GREEN
                        if self._cache["HIGHSCORE_TEXT"].text is not None:
                            self._cache["HIGHSCORE_TEXT"].text.color = WHITE
                    elif self._cache["INSTRUCTIONS"].contains(event.pos[0],
                                                              event.pos[1]):
                        self._cache["INSTRUCTIONS"].color = GREEN
                        self._cache["INSTRUCTIONS_TEXT"].color = GREEN
                        if self._cache["INSTRUCTIONS_TEXT"].text is not None:
                            self._cache["INSTRUCTIONS_TEXT"].text.color = WHITE
                    elif self._cache["EXIT"].contains(event.pos[0],
                                                      event.pos[1]):
                        self._cache["EXIT"].color = GREEN
                        self._cache["EXIT_TEXT"].color = GREEN
                        if self._cache["EXIT_TEXT"].text is not None:
                            self._cache["EXIT_TEXT"].text.color = WHITE
                    else:
                        self._cache["PLAY"].color = YELLOW
                        self._cache["PLAY_TEXT"].color = YELLOW
                        if self._cache["PLAY_TEXT"].text is not None:
                            self._cache["PLAY_TEXT"].text.color = BLACK
                        self._cache["HIGHSCORE"].color = YELLOW
                        self._cache["HIGHSCORE_TEXT"].color = YELLOW
                        if self._cache["HIGHSCORE_TEXT"].text is not None:
                            self._cache["HIGHSCORE_TEXT"].text.color = BLACK
                        self._cache["INSTRUCTIONS"].color = YELLOW
                        self._cache["INSTRUCTIONS_TEXT"].color = YELLOW
                        if self._cache["INSTRUCTIONS_TEXT"].text is not None:
                            self._cache["INSTRUCTIONS_TEXT"].text.color = BLACK
                        self._cache["EXIT"].color = YELLOW
                        self._cache["EXIT_TEXT"].color = YELLOW
                        if self._cache["EXIT_TEXT"].text is not None:
                            self._cache["EXIT_TEXT"].text.color = BLACK
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    # def _remove_cache(self, name: str) -> None:
    #    del self._cache[name]

    def _gen_layout(self) -> None:
        self.layout.add_rect(xp=0, yp=15, widthp=25,
                             heightp=10, name="PLAY")
        self.layout.add_rect(xp=0, yp=18, widthp=25,
                             heightp=4, name="PLAY_TEXT",
                             text="PLAY")
        self.layout.center_rect_x("PLAY")
        self.layout.center_rect_x("PLAY_TEXT")
        # print(self.layout.get_rect_absolute("PLAY_TEXT",
        #      width=self._width, height=self._height).text.scale)
        self.layout.add_rect(xp=0, yp=30, widthp=25,
                             heightp=10, name="HIGHSCORE")
        self.layout.add_rect(xp=0, yp=33, widthp=25,
                             heightp=4, name="HIGHSCORE_TEXT",
                             text="HIGHSCORE")
        self.layout.center_rect_x("HIGHSCORE")
        self.layout.center_rect_x("HIGHSCORE_TEXT")
        # print(self.layout.get_rect_absolute("HIGHSCORE_TEXT",
        #      width=self._width, height=self._height).text.scale)
        self.layout.add_rect(xp=0, yp=45, widthp=25,
                             heightp=10, name="INSTRUCTIONS")
        self.layout.add_rect(xp=0, yp=48, widthp=25,
                             heightp=4, name="INSTRUCTIONS_TEXT",
                             text="INSTRUCTIONS")
        self.layout.center_rect_x("INSTRUCTIONS")
        self.layout.center_rect_x("INSTRUCTIONS_TEXT")
        # print(self.layout.get_rect_absolute("INSTRUCTIONS_TEXT",
        #      width=self._width, height=self._height).text.scale)
        self.layout.add_rect(xp=0, yp=60, widthp=25,
                             heightp=10, name="EXIT")
        self.layout.add_rect(xp=0, yp=63, widthp=25,
                             heightp=4, name="EXIT_TEXT",
                             text="EXIT")
        self.layout.center_rect_x("EXIT")
        self.layout.center_rect_x("EXIT_TEXT")
        # print(self.layout.get_rect_absolute("EXIT_TEXT",
        #      width=self._width, height=self._height).text.scale)

    def _cache_abs_layout(self) -> None:
        for abs_rect in self.layout.get_all_rects_absolute(self._width,
                                                           self._height):
            abs_rect.color = YELLOW
            if abs_rect.text is not None:
                abs_rect.text.color = BLACK
            self._cache[abs_rect.name] = abs_rect

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.clear(self._backgroung_color)
        for abs_rect in self._cache.values():
            self.graphics.draw_rectangle(
                x=abs_rect.x,
                y=abs_rect.y,
                width=abs_rect.width,
                height=abs_rect.height,
                color=abs_rect.color
            )
            if abs_rect.text is not None:
                self.graphics.draw_text(
                    text=abs_rect.text.text,
                    x=abs_rect.text.x,
                    y=abs_rect.text.y,
                    color=abs_rect.text.color,
                    background_color=abs_rect.color,
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )
        # self.graphics.draw_text("NADPIS", 100, 100, YELLOW, scale=10)
        self.graphics.refresh()
        return self._self_app_state
