from ..highscores import HighscoreStore
from ..models import AppState
from .events import Event, EventType
from .graphics import Graphics
from .layout import (
    AbsoluteRect,
    BLACK,
    Layout,
    WHITE,
    YELLOW,
    fit_text_group_scale,
    percent_rect,
    text_box_layout,
)
from .screen_base import Screen


class HighscoresScreen(Screen):
    """Highscores screen."""

    def __init__(
        self,
        graphics: Graphics,
    ) -> None:
        """Build and cache the highscores layout for the graphics window."""
        self.graphics = graphics
        self.store: HighscoreStore | None = None
        self._self_app_state = AppState.HIGHSCORES

        sizes = self.graphics.get_window_size()
        self._width = sizes[0]
        self._height = sizes[1]

        self.layout = Layout()
        self._cache: dict[str, AbsoluteRect] = {}

        self._gen_layout()
        self._cache_abs_layout()

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
        """Handle input events."""
        if event.type == EventType.KEY_ESC:
            return AppState.MAIN_MENU
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.fill(BLACK)
        self.graphics.set_layer_order(["main"])

        for abs_rect in self._cache.values():
            if abs_rect.text is not None:
                self.graphics.draw_text(
                    text=abs_rect.text.text,
                    x=abs_rect.text.x,
                    y=abs_rect.text.y,
                    color=abs_rect.text.color,
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )

        entries = self.store.entries if self.store is not None else []
        rows = [
            f"{index + 1:2} {entry['name'].upper():10} {entry['score']}"
            for index, entry in enumerate(entries)
        ] or ['NO HIGHSCORES YET']

        first_box = percent_rect(
            self._width,
            self._height,
            10,
            25,
            80,
            5.5,
        )
        row_scale = fit_text_group_scale(
            rows,
            first_box[2],
            first_box[3],
            padding_xp=2,
            padding_yp=10,
        )

        for index, text in enumerate(rows):
            row_box = percent_rect(
                self._width,
                self._height,
                10,
                25 + index * 5.5,
                80,
                5.5,
            )
            text_x, text_y, scale, spacing = text_box_layout(
                text,
                *row_box,
                padding_xp=2,
                padding_yp=10,
                scale=row_scale,
            )
            self.graphics.draw_text(
                text,
                text_x,
                text_y,
                WHITE,
                scale=scale,
                spacing=spacing,
            )

        if self.store is not None and self.store.error:
            error = 'HIGHSCORE FILE ERROR - SEE CONSOLE'
            error_box = percent_rect(
                self._width,
                self._height,
                5,
                86,
                90,
                6,
            )
            text_x, text_y, scale, spacing = text_box_layout(
                error,
                *error_box,
                padding_xp=3,
                padding_yp=10,
            )
            self.graphics.draw_text(
                error,
                text_x,
                text_y,
                YELLOW,
                scale=scale,
                spacing=spacing,
            )

        self.graphics.refresh()
        return self._self_app_state

    def _gen_layout(self) -> None:
        """Add percentage-based title and return-instruction rectangles."""
        self.layout.add_rect(
            xp=0,
            yp=9,
            widthp=100,
            heightp=7,
            name="TITLE",
            text="HIGHSCORES",
            x_offsetp=4,
            y_offsetp=15,
            x_offsetp_rev=4,
            y_offsetp_rev=15,
        )
        self.layout.center_rect_x("TITLE")

        self.layout.add_rect(
            xp=0,
            yp=94,
            widthp=100,
            heightp=4,
            name="BACK_INFO",
            text="press esc to go back to main menu",
            x_offsetp=4,
            y_offsetp=10,
            x_offsetp_rev=4,
            y_offsetp_rev=10,
        )
        self.layout.center_rect_x("BACK_INFO")

    def _cache_abs_layout(self) -> None:
        """Cache responsive geometry and text colors for static labels."""
        for name in ("TITLE", "BACK_INFO"):
            abs_rect = self.layout.get_rect_absolute(
                name,
                self._width,
                self._height,
            )
            if abs_rect is None:
                continue

            abs_rect.color = BLACK
            if abs_rect.text is not None:
                abs_rect.text.color = (
                    YELLOW if name == "TITLE" else WHITE
                )
            self._cache[name] = abs_rect
