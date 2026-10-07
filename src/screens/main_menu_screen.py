from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..ui import YELLOW, BLACK, BLUE, PURPLE, ORANGE, WHITE, Layout, AbsoluteRect, NORMAL_TEXT_SCALE
from ..events import Event, EventType
from ..highscores import HighscoreStore


BACKGROUND_COLOR = BLACK
DEF_RECT_COLOR = YELLOW
DEF_TEXT_COLOR = BLUE
REV_RECT_COLOR = PURPLE
REV_TEXT_COLOR = ORANGE


class MainMenuScreen(Screen):
    """Main application menu."""

    def __init__(self, graphics: Graphics) -> None:
        """Build the menu layout and highlight the initial button."""
        self.graphics = graphics
        self.store: HighscoreStore | None = None
        self.layout = Layout()
        self._self_app_state = AppState.MAIN_MENU

        sizes = self.graphics.get_window_size()
        self._width: int = sizes[0]
        self._height: int = sizes[1]
        self._cache: dict[str, AbsoluteRect] = {}
        # Each button is (layout name, visible label, destination state).
        self._buttons: list[tuple[str, str, AppState]] = [
            ('GAME', 'PLAY', AppState.GAME),
            ('HIGHSCORES', 'HIGHSCORES', AppState.HIGHSCORES),
            ('INSTRUCTIONS', 'INSTRUCTIONS', AppState.INSTRUCTIONS),
            ('EXIT', 'EXIT', AppState.EXIT),
        ]
        self._gen_layout()
        self._cache_abs_layout()
        self._selected = 0
        self._set_rect_colors(self._buttons[self._selected][0], True)

    def handle_event(self, event: Event) -> AppState:
        """Handle an input event."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_UP:
            if self._selected > 0:
                self._set_rect_colors(self._buttons[self._selected][0], False)
                self._selected -= 1
                self._set_rect_colors(self._buttons[self._selected][0], True)
        elif event.type == EventType.KEY_DOWN:
            if self._selected < len(self._buttons) - 1:
                self._set_rect_colors(self._buttons[self._selected][0], False)
                self._selected += 1
                self._set_rect_colors(self._buttons[self._selected][0], True)
        elif event.type == EventType.KEY_ENTER:
            return self._buttons[self._selected][2]
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render the screen."""

        self.graphics.fill(BLACK)
        self.graphics.set_layer_order(["main"])
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
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )
        if self.store is not None and self.store.entries:
            best = self.store.entries[0]
            text = f"BEST {best['name'].upper()} {best['score']}"
            scale = NORMAL_TEXT_SCALE
            self.graphics.draw_text(
                text, max(10, (self._width - len(text) * 6 * scale) // 2),
                self._height // 12, WHITE, scale=scale, spacing=scale)
        self.graphics.refresh()
        return self._self_app_state

    def _set_rect_colors(self, name: str, hovered: bool) -> None:
        """Apply selected or default colors to the named cached button."""
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

    def _gen_layout(self) -> None:
        """Build centered menu buttons and the keyboard navigation hint."""
        for index, (name, label, _) in enumerate(self._buttons):
            self.layout.add_rect(xp=0, yp=20 + 15 * index, widthp=25,
                                 heightp=10, name=name, text=label,
                                 x_offsetp=5, x_offsetp_rev=5)
            self.layout.center_rect_x(name)
        self.layout.add_rect(xp=0, yp=95, widthp=100,
                             heightp=2, name="CONTROL_INFO",
                             text="use arrow up and down to move",)
        self.layout.center_rect_x("CONTROL_INFO")

    def _cache_abs_layout(self) -> None:
        """Cache pixel geometry with shared button scale and default colors."""
        for button_name, _, _ in self._buttons:
            abs_rect = self.layout.get_rect_absolute(button_name,
                                                     self._width,
                                                     self._height,
                                                     NORMAL_TEXT_SCALE)
            if abs_rect is None:
                continue
            abs_rect.color = DEF_RECT_COLOR
            if abs_rect.text is not None:
                abs_rect.text.color = DEF_TEXT_COLOR
            self._cache[abs_rect.name] = abs_rect
        abs_control_info = self.layout.get_rect_absolute("CONTROL_INFO",
                                                         self._width,
                                                         self._height,
                                                         NORMAL_TEXT_SCALE)
        if abs_control_info is not None:
            abs_control_info.color = BLACK
            if abs_control_info.text is not None:
                abs_control_info.text.color = WHITE
            self._cache["CONTROL_INFO"] = abs_control_info
