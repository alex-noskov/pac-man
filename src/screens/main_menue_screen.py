import pygame
import time
from .screen import Screen
from ..models import AppState
# from ..graphics import Graphics
from ..graphics import Graphics
from ..colors import YELLOW, BLACK, BLUE, PURPLE, ORANGE
from ..ui import Layout, AbsoluteRect


BACKGROUND_COLOR = BLACK
DEF_RECT_COLOR = YELLOW
DEF_TEXT_COLOR = BLUE
REV_RECT_COLOR = PURPLE
REV_TEXT_COLOR = ORANGE


class MainMenuScreen(Screen):
    """Main application menu."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self.layout = Layout()
        self._self_app_state = AppState.MAIN_MENU
        print("EST CONTACT!")
        # sizes = self.graphics.get_window_size()
        # self._width: int = sizes[0]
        # self._height: int = sizes[1]
        # self._cache: dict[str, AbsoluteRect] = {}
        # self._hovered_rect: str | None = None
        # self._gen_layout()
        # self._cache_abs_layout()

    def _set_rect_colors(self, name: str, hovered: bool) -> None:
        rect = self._cache.get(name)
        if rect is None:
            return
        if hovered:
            rect.color = REV_RECT_COLOR
            text_color = REV_TEXT_COLOR
        else:
            rect.color = DEF_RECT_COLOR
            text_color = DEF_TEXT_COLOR
        if rect.text is not None:
            rect.text.color = text_color

    def handle_event(self, event: pygame.event.Event) -> AppState:
        """Handle an input event."""
        if event.type == pygame.QUIT:
            print(event)
            return AppState.EXIT
        if event.type == pygame.MOUSEMOTION:
            hovered_rect = None
            for abs_rect in self._cache.values():
                if abs_rect.contains(event.pos[0], event.pos[1]):
                    hovered_rect = abs_rect.name
                    break
            if hovered_rect != self._hovered_rect:
                if self._hovered_rect is not None:
                    self._set_rect_colors(
                        self._hovered_rect,
                        hovered=False
                    )
                if hovered_rect is not None:
                    self._set_rect_colors(
                        hovered_rect,
                        hovered=True
                    )
                self._hovered_rect = hovered_rect
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    # def _remove_cache(self, name: str) -> None:
    #    del self._cache[name]

    def _gen_layout(self) -> None:
        self.layout.add_rect(xp=0, yp=15, widthp=25,
                             heightp=10, name="PLAY", text="PLAY",
                             x_offsetp=5, x_offsetp_rev=5)
        self.layout.center_rect_x("PLAY")
        # print(self.layout.get_rect_absolute("PLAY_TEXT",
        #      width=self._width, height=self._height).text.scale)
        self.layout.add_rect(xp=0, yp=30, widthp=25,
                             heightp=10, name="HIGHSCORE", text="HIGHSCORE",
                             x_offsetp=5, x_offsetp_rev=5)
        self.layout.center_rect_x("HIGHSCORE")
        self.layout.add_rect(xp=0, yp=45, widthp=25,
                             heightp=10, name="INSTRUCTIONS",
                             text="INSTRUCTIONS", x_offsetp=5, x_offsetp_rev=5)
        self.layout.center_rect_x("INSTRUCTIONS")
        abs_instructions = self.layout.get_rect_absolute("INSTRUCTIONS",
                                                         width=self._width,
                                                         height=self._height)
        if abs_instructions is not None and abs_instructions.text is not None:
            self._menu_scale = abs_instructions.text.scale
        print("MAIN MENUE SCALE:", self._menu_scale)
        # print(self.layout.get_rect_absolute("INSTRUCTIONS_TEXT",
        #      width=self._width, height=self._height).text.scale)
        self.layout.add_rect(xp=0, yp=60, widthp=25,
                             heightp=10, name="EXIT", text="EXIT",
                             x_offsetp=5, x_offsetp_rev=5)
        self.layout.center_rect_x("EXIT")
        # print(self.layout.get_rect_absolute("EXIT_TEXT",
        #      width=self._width, height=self._height).text.scale)

    def _cache_abs_layout(self) -> None:
        for abs_rect in self.layout.get_all_rects_absolute(self._width,
                                                           self._height,
                                                           self._menu_scale):
            abs_rect.color = DEF_RECT_COLOR
            if abs_rect.text is not None:
                abs_rect.text.color = DEF_TEXT_COLOR
            self._cache[abs_rect.name] = abs_rect

    def render(self) -> AppState:
        """Render the screen."""
        t = time.perf_counter()
        self.graphics.clear(BACKGROUND_COLOR)
        t1 = time.perf_counter()
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
        t2 = time.perf_counter()
        # self.graphics.draw_text("NADPIS", 100, 100, YELLOW, scale=10)
        self.graphics.refresh()
        t3 = time.perf_counter()
        print(
            f"clear={t1-t:.6f} "
            f"draw={t2-t1:.6f} "
            f"refresh={t3-t2:.6f}"
        )
        return self._self_app_state
