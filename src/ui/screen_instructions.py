from ..models import AppState
from .colors import BLACK, NORMAL_TEXT_SCALE, WHITE, YELLOW
from .events import Event, EventType
from .graphics import Graphics
from .layout import AbsoluteRect, Layout
from .screen_base import Screen


class InstructionsScreen(Screen):
    """Instructions screen."""

    def __init__(
        self,
        graphics: Graphics,
    ) -> None:
        """Build gameplay instructions and cache their window-sized layout."""
        self.graphics = graphics
        self._self_app_state = AppState.INSTRUCTIONS

        sizes = self.graphics.get_window_size()
        self._width = sizes[0]
        self._height = sizes[1]

        self.layout = Layout()
        self._cache: dict[str, AbsoluteRect] = {}

        self._instructions = [
            "USE ARROW KEYS / WASD TO MOVE",
            "EAT DOTS TO SCORE POINTS",
            "EAT ALL DOTS TO COMPLETE THE LEVEL",
            "AVOID THE GHOSTS",
            "TOUCHING A GHOST COSTS ONE LIFE",
            "YOU START WITH A LIMITED NUMBER OF LIVES",
            "POWER PELLETS MAKE GHOSTS VULNERABLE",
            "EAT VULNERABLE GHOSTS FOR BONUS POINTS",
            "ESC OR P PAUSES - ENTER RESUMES",
            "C TOGGLES EVALUATION CHEATS",
            "CHEATS I INVINCIBLE N SKIP F FREEZE",
            "CHEATS L LIFE B SPEED V POWER",
            "CLEAR THE MAZE TO ADVANCE",
            "LOSE ALL LIVES AND THE GAME IS OVER",
            "CLEAR ALL 10 LEVELS TO WIN",
        ]

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

        self.graphics.refresh()
        return self._self_app_state

    def _gen_layout(self) -> None:
        """Arrange instructions and the return hint in percentage space."""
        line_height = 4
        line_spacing = 1

        total_height = (
            len(self._instructions) * line_height
            + (len(self._instructions) - 1) * line_spacing
        )

        # Move the instruction block slightly above the center.
        start_y = (100 - total_height) / 2 - 5

        for index, text in enumerate(self._instructions):
            name = f"INSTRUCTION_{index}"
            self.layout.add_rect(
                xp=0,
                yp=start_y + index * (line_height + line_spacing),
                widthp=100,
                heightp=line_height,
                name=name,
                text=text,
            )
            self.layout.center_rect_x(name)

        # Bottom "press esc..." message.
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
        """Cache pixel geometry and text colors for the instruction labels."""
        for name in self.layout.get_rect_names():
            abs_rect = self.layout.get_rect_absolute(
                name,
                self._width,
                self._height,
                NORMAL_TEXT_SCALE,
            )
            if abs_rect is None:
                continue

            abs_rect.color = BLACK
            if abs_rect.text is not None:
                if name == "BACK_INFO":
                    abs_rect.text.color = WHITE
                else:
                    abs_rect.text.color = YELLOW
            self._cache[name] = abs_rect
