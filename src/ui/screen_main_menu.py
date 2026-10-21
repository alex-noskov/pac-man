from ..highscores import HighscoreStore
from ..models import AppState
from .events import Event, EventType
from .graphics import Graphics
from .layout import (
    AbsoluteRect,
    BLACK,
    BLUE,
    Layout,
    ORANGE,
    PURPLE,
    WHITE,
    YELLOW,
    percent_rect,
    text_box_layout,
)
from .screen_base import Screen


BACKGROUND_COLOR = BLACK
DEF_RECT_COLOR = YELLOW
DEF_TEXT_COLOR = BLUE
REV_RECT_COLOR = PURPLE
REV_TEXT_COLOR = ORANGE


class MainMenuScreen(Screen):
    """Main application menu."""

    def __init__(
        self,
        graphics: Graphics,
    ) -> None:
        """Build the menu layout and highlight the initial button."""
        self.graphics = graphics
        self.store: HighscoreStore | None = None
        self.layout = Layout()
        self._self_app_state = AppState.MAIN_MENU

        sizes = self.graphics.get_window_size()
        self._width: int = sizes[0]
        self._height: int = sizes[1]
        self._cache: dict[str, AbsoluteRect] = {}
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

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
        """Handle an input event."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_UP:
            self._set_rect_colors(
                self._buttons[self._selected][0],
                False,
            )
            self._selected = (self._selected - 1) % len(self._buttons)
            self._set_rect_colors(
                self._buttons[self._selected][0],
                True,
            )
        elif event.type == EventType.KEY_DOWN:
            self._set_rect_colors(
                self._buttons[self._selected][0],
                False,
            )
            self._selected = (self._selected + 1) % len(self._buttons)
            self._set_rect_colors(
                self._buttons[self._selected][0],
                True,
            )
        elif event.type == EventType.KEY_ENTER:
            return self._buttons[self._selected][2]
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.fill(BACKGROUND_COLOR)
        self.graphics.set_layer_order(["main"])

        for abs_rect in self._cache.values():
            self.graphics.draw_rectangle(
                x=abs_rect.x,
                y=abs_rect.y,
                width=abs_rect.width,
                height=abs_rect.height,
                color=abs_rect.color,
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
            box = percent_rect(
                self._width,
                self._height,
                10,
                4,
                80,
                8,
            )
            text_x, text_y, scale, spacing = text_box_layout(
                text,
                *box,
                padding_xp=3,
                padding_yp=15,
            )
            self.graphics.draw_text(
                text,
                text_x,
                text_y,
                WHITE,
                scale=scale,
                spacing=spacing,
            )

        self.graphics.refresh()
        return self._self_app_state

    def _set_rect_colors(
        self,
        name: str,
        hovered: bool,
    ) -> None:
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
            self.layout.add_rect(
                xp=0,
                yp=20 + 15 * index,
                widthp=25,
                heightp=10,
                name=name,
                text=label,
                x_offsetp=5,
                y_offsetp=20,
                x_offsetp_rev=5,
                y_offsetp_rev=20,
            )
            self.layout.center_rect_x(name)

        self.layout.add_rect(
            xp=0,
            yp=94,
            widthp=100,
            heightp=4,
            name="CONTROL_INFO",
            text="use arrow up and down to move",
            x_offsetp=4,
            y_offsetp=10,
            x_offsetp_rev=4,
            y_offsetp_rev=10,
        )
        self.layout.center_rect_x("CONTROL_INFO")

    def _cache_abs_layout(self) -> None:
        """Cache responsive geometry with one shared button text scale."""
        button_names = [name for name, _, _ in self._buttons]
        button_scale = self.layout.get_shared_text_scale(
            button_names,
            self._width,
            self._height,
        )

        for button_name in button_names:
            abs_rect = self.layout.get_rect_absolute(
                button_name,
                self._width,
                self._height,
                button_scale,
            )
            if abs_rect is None:
                continue
            abs_rect.color = DEF_RECT_COLOR
            if abs_rect.text is not None:
                abs_rect.text.color = DEF_TEXT_COLOR
            self._cache[abs_rect.name] = abs_rect

        control = self.layout.get_rect_absolute(
            "CONTROL_INFO",
            self._width,
            self._height,
        )
        if control is not None:
            control.color = BLACK
            if control.text is not None:
                control.text.color = WHITE
            self._cache["CONTROL_INFO"] = control
