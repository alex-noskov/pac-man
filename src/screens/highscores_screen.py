from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..events import Event, EventType
from ..ui import WHITE, BLACK, YELLOW, Layout, AbsoluteRect, NORMAL_TEXT_SCALE, TITLE_TEXT_SCALE
from ..highscores import HighscoreStore


class HighscoresScreen(Screen):
    """Highscores screen."""

    def __init__(self, graphics: Graphics) -> None:
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

    def handle_event(self, event: Event) -> AppState:
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
        rows = [f"{i + 1:2} {e['name'].upper():10} {e['score']}"
                for i, e in enumerate(entries)] or ['NO HIGHSCORES YET']
        for index, text in enumerate(rows):
            scale = NORMAL_TEXT_SCALE
            self.graphics.draw_text(
                text, max(10, (self._width - len(text) * 6 * scale) // 2),
                self._height // 4 + index * self._height // 18,
                WHITE, scale=scale, spacing=scale)
        if self.store is not None and self.store.error:
            self.graphics.draw_text('HIGHSCORE FILE ERROR - SEE CONSOLE',
                                    10, self._height * 9 // 10, YELLOW,
                                    scale=NORMAL_TEXT_SCALE,
                                    spacing=NORMAL_TEXT_SCALE)
        self.graphics.refresh()

        return self._self_app_state

    def _gen_layout(self) -> None:
        """Add percentage-based title and return-instruction rectangles."""
        # Title rectangle starts 10% down from the top.
        self.layout.add_rect(
            xp=0,
            yp=10,
            widthp=100,
            heightp=5,
            name="TITLE",
            text="HIGHSCORES",
        )
        self.layout.center_rect_x("TITLE")

        # Return hint near the bottom of the window.
        self.layout.add_rect(
            xp=0,
            yp=95,
            widthp=100,
            heightp=2,
            name="BACK_INFO",
            text="press esc to go back to main menue",
        )
        self.layout.center_rect_x("BACK_INFO")

    def _cache_abs_layout(self) -> None:
        """Cache pixel geometry and text colors for the static labels."""
        for name in ("TITLE", "BACK_INFO"):
            abs_rect = self.layout.get_rect_absolute(
                name,
                self._width,
                self._height,
                TITLE_TEXT_SCALE if name == 'TITLE' else NORMAL_TEXT_SCALE,
            )

            if abs_rect is None:
                continue

            abs_rect.color = BLACK

            if abs_rect.text is not None:
                if name == "TITLE":
                    abs_rect.text.color = YELLOW
                else:
                    abs_rect.text.color = WHITE

            self._cache[name] = abs_rect
