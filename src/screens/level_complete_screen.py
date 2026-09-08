from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..colors import WHITE, BLACK, YELLOW
from ..events import Event, EventType
from ..ui import Layout, AbsoluteRect


class LevelCompleteScreen(Screen):
    """Level complete screen."""

    def __init__(self, graphics: Graphics) -> None:
        self.graphics = graphics
        self._self_app_state = AppState.LEVEL_COMPLETE

        sizes = self.graphics.get_window_size()
        self._width = sizes[0]
        self._height = sizes[1]

        self.layout = Layout()
        self._cache: dict[str, AbsoluteRect] = {}

        self._gen_layout()
        self._cache_abs_layout()

    def handle_event(self, event: Event) -> AppState:
        """Handle input events."""

        if event.type == EventType.KEY_ENTER:
            return AppState.GAME

        if event.type == EventType.KEY_ESC:
            return AppState.MAIN_MENU

        if event.type == EventType.CLOSE:
            return AppState.EXIT

        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render the level complete screen."""

        self.graphics.clear()
        self.graphics.fill(BLACK)
        self.graphics.set_layer_order(["main"])

        for abs_rect in self._cache.values():
            # Draw yellow rectangle.
            self.graphics.draw_rectangle(
                x=abs_rect.x,
                y=abs_rect.y,
                width=abs_rect.width,
                height=abs_rect.height,
                color=YELLOW,
            )

            # Draw centered text.
            if abs_rect.text is not None:
                self.graphics.draw_text(
                    text=abs_rect.text.text,
                    x=abs_rect.text.x,
                    y=abs_rect.text.y,
                    color=WHITE,
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )

        self.graphics.refresh()

        return self._self_app_state

    def _gen_layout(self) -> None:
        """Generate the level complete rectangle."""

        self.layout.add_rect(
            xp=25,
            yp=40,
            widthp=50,
            heightp=20,
            name="LEVEL_COMPLETE",
            text="LEVEL COMPLETE!",
        )

        # Center rectangle horizontally.
        self.layout.center_rect_x("LEVEL_COMPLETE")

    def _cache_abs_layout(self) -> None:
        """Cache absolute geometry."""

        abs_rect = self.layout.get_rect_absolute(
            "LEVEL_COMPLETE",
            self._width,
            self._height,
        )

        if abs_rect is None:
            return

        abs_rect.color = YELLOW

        if abs_rect.text is not None:
            abs_rect.text.color = WHITE

        self._cache["LEVEL_COMPLETE"] = abs_rect
