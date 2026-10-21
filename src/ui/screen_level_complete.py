import math
import time

from ..models import AppState
from .events import Event, EventType
from .graphics import Graphics
from .layout import (
    AbsoluteRect,
    BLACK,
    GRAY,
    Layout,
    NORMAL_TEXT_SCALE,
    TITLE_TEXT_SCALE,
    YELLOW,
    AUTO_CONTINUE_DELAY,
    responsive_scale,
)
from .screen_base import Screen


class LevelCompleteScreen(Screen):
    """Level complete screen."""

    def __init__(
        self,
        graphics: Graphics,
    ) -> None:
        """Build and cache the level-complete layout for the window."""
        self.graphics = graphics
        self._self_app_state = AppState.LEVEL_COMPLETE

        self._started_at = time.monotonic()

        sizes = self.graphics.get_window_size()
        self._width = sizes[0]
        self._height = sizes[1]

        self.layout = Layout()
        self._cache: dict[str, AbsoluteRect] = {}

        self._gen_layout()
        self._cache_abs_layout()

    def begin(self) -> None:
        """Restart the automatic next-level countdown."""
        self._started_at = time.monotonic()

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
        """Handle input events."""
        if event.type == EventType.KEY_ENTER:
            return AppState.GAME
        if event.type == EventType.CLOSE:
            return AppState.EXIT

        return self._self_app_state

    def update(self) -> AppState:
        """Automatically continue after a short delay."""
        elapsed = time.monotonic() - self._started_at

        if elapsed >= AUTO_CONTINUE_DELAY:
            return AppState.GAME

        return self._self_app_state

    def render(self) -> AppState:
        """Render the level complete screen and countdown."""
        self.graphics.fill(BLACK)
        self.graphics.set_layer_order(["main"])

        for abs_rect in self._cache.values():
            self.graphics.draw_rectangle(
                x=abs_rect.x,
                y=abs_rect.y,
                width=abs_rect.width,
                height=abs_rect.height,
                color=YELLOW,
            )

            if abs_rect.text is not None:
                self.graphics.draw_text(
                    text=abs_rect.text.text,
                    x=abs_rect.text.x,
                    y=abs_rect.text.y,
                    color=BLACK,
                    spacing=abs_rect.text.spacing,
                    scale=abs_rect.text.scale,
                )

        elapsed = time.monotonic() - self._started_at
        remaining = max(
            1,
            math.ceil(AUTO_CONTINUE_DELAY - elapsed),
        )

        hint = f"NEXT LEVEL IN {remaining} - ENTER TO CONTINUE"

        scale = responsive_scale(
            self._width,
            self._height,
            NORMAL_TEXT_SCALE,
        )
        spacing = scale

        text_width = (
            len(hint) * 5 * scale
            + max(0, len(hint) - 1) * spacing
        )

        self.graphics.draw_text(
            text=hint,
            x=(self._width - text_width) // 2,
            y=int(self._height * 0.64),
            color=GRAY,
            spacing=spacing,
            scale=scale,
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
            responsive_scale(
                self._width,
                self._height,
                TITLE_TEXT_SCALE,
            ),
        )
        if abs_rect is None:
            return

        abs_rect.color = YELLOW
        if abs_rect.text is not None:
            abs_rect.text.color = BLACK
        self._cache["LEVEL_COMPLETE"] = abs_rect
