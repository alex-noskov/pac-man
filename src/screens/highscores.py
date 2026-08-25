from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..colors import WHITE, BLACK, YELLOW
from ..events import Event, EventType
from ..ui import Layout, AbsoluteRect


class HighscoresScreen(Screen):
    """Highscores screen."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self.self_app_state = AppState.HIGHSCORES

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

        # if event.type == EventType.CLOSE:
        #    return AppState.EXIT

        return self.self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self.self_app_state

    def render(self) -> AppState:
        """Render the screen."""
        self.graphics.clear()

        for abs_rect in self._cache.values():
            if abs_rect.text is not None:
                self.graphics.draw_text(
                    text=abs_rect.text.text,
                    x=abs_rect.text.x,
                    y=abs_rect.text.y,
                    color=abs_rect.text.color,
                    background_color=BLACK,
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )

        self.graphics.refresh()

        return self.self_app_state

    def _gen_layout(self) -> None:
        # HIGHSCORES title: 20% down from the top.
        self.layout.add_rect(
            xp=0,
            yp=10,
            widthp=100,
            heightp=5,
            name="TITLE",
            text="HIGHSCORES",
        )
        self.layout.center_rect_x("TITLE")

        # Instructions: 5% up from the bottom.
        # heightp=5 means the rectangle occupies the bottom 5%.
        # Therefore yp=90 places it in the 90%-95% range.
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
                if name == "TITLE":
                    abs_rect.text.color = YELLOW
                else:
                    abs_rect.text.color = WHITE

            self._cache[name] = abs_rect
