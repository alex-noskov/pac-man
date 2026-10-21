"""Victory/loss score presentation and keyboard player-name entry."""
from ..highscores import HighscoreStore
from ..models import AppState
from .layout import (
    BLACK,
    NORMAL_TEXT_SCALE,
    TITLE_TEXT_SCALE,
    WHITE,
    YELLOW,
    responsive_px,
    responsive_scale,
    text_box_layout,
)
from .events import Event, EventType
from .graphics import Graphics
from .screen_base import Screen

NAME_BOX_WIDTH = 600
NAME_BOX_HEIGHT = 48
NAME_BOX_Y = 280
SAVE_BUTTON_WIDTH = 560
SAVE_BUTTON_HEIGHT = 48
SAVE_BUTTON_Y = 390


class EndScreen(Screen):
    """Display an outcome and save one score with recoverable I/O errors."""

    def __init__(
        self,
        graphics: Graphics,
        store: HighscoreStore,
        state: AppState,
    ) -> None:
        """Bind shared graphics/storage to a specific win or loss screen."""
        self.graphics = graphics
        self.store = store
        self.state = state
        self.begin(0)

    def begin(
        self,
        score: int,
    ) -> None:
        """Reset editing and submission state for each completed run."""
        self.score = score
        self.name = ''
        self.message = ''
        self._added = False

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
        """Edit a validated ten-character name, save, retry, or leave."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_ESC:
            return AppState.MAIN_MENU
        if event.type == EventType.TEXT and not self._added:
            text = str(event.data.get('text', ''))
            filtered = ''.join(
                character
                for character in text
                if character.isascii()
                and (character.isalnum() or character == ' ')
            )
            self.name = (self.name + filtered)[:10]
        elif event.type == EventType.KEY_BACKSPACE and not self._added:
            self.name = self.name[:-1]
        elif event.type == EventType.KEY_ENTER:
            if not self._added:
                self._added = self.store.add(
                    self.name.strip() or 'PLAYER',
                    self.score,
                )
            if self._added and self.store.save():
                return AppState.MAIN_MENU
            self.message = self.store.error
        return self.state

    def update(self) -> AppState:
        """Keep the finished score and all gameplay timers frozen."""
        return self.state

    def render(self) -> AppState:
        """Present a responsive keyboard field and save confirmation."""
        g = self.graphics
        width, height = g.get_window_size()
        normal_scale = responsive_scale(
            width,
            height,
            NORMAL_TEXT_SCALE,
        )

        g.set_layer_order(['main'])
        g.fill(BLACK)

        self._line(
            'VICTORY - CONGRATULATIONS'
            if self.state == AppState.VICTORY
            else 'GAME OVER',
            responsive_px(width, height, 70),
            YELLOW,
            TITLE_TEXT_SCALE,
        )
        self._line(
            f'FINAL SCORE {self.score}',
            responsive_px(width, height, 126),
        )
        self._line(
            'TYPE ON YOUR KEYBOARD TO ENTER YOUR NAME',
            responsive_px(width, height, 194),
        )
        self._line(
            'SAVE FAILED - ENTER TO RETRY'
            if self.message
            else 'MAX 10: LETTERS / DIGITS / SPACES',
            responsive_px(width, height, 238),
            YELLOW,
        )

        box_width = responsive_px(
            width,
            height,
            NAME_BOX_WIDTH,
        )
        box_height = responsive_px(
            width,
            height,
            NAME_BOX_HEIGHT,
        )
        top = responsive_px(
            width,
            height,
            NAME_BOX_Y,
        )
        left = (width - box_width) // 2

        border = responsive_px(width, height, 2)
        g.draw_rectangle(
            left,
            top,
            box_width,
            box_height,
            YELLOW,
        )
        g.draw_rectangle(
            left + border,
            top + border,
            box_width - 2 * border,
            box_height - 2 * border,
            0xFF18243B,
        )

        text = self.name.upper() if self.name else 'TYPE YOUR NAME HERE'
        padding_x = responsive_px(width, height, 24)
        padding_y = responsive_px(width, height, 8)
        text_x, text_y, field_scale, spacing = text_box_layout(
            text,
            left,
            top,
            box_width,
            box_height,
            normal_scale,
            padding_x,
            padding_y,
        )

        g.draw_text(
            text,
            text_x,
            text_y,
            WHITE,
            scale=field_scale,
            spacing=spacing,
        )

        if self.name and not self._added:
            cursor_width = responsive_px(width, height, 2)
            cursor_gap = responsive_px(width, height, 2)
            text_width = (
                len(text) * 5 * field_scale
                + max(0, len(text) - 1) * spacing
            )
            g.draw_rectangle(
                text_x + text_width + cursor_gap,
                text_y,
                cursor_width,
                8 * field_scale,
                YELLOW,
            )

        button_width = responsive_px(
            width,
            height,
            SAVE_BUTTON_WIDTH,
        )
        button_height = responsive_px(
            width,
            height,
            SAVE_BUTTON_HEIGHT,
        )
        button_top = responsive_px(
            width,
            height,
            SAVE_BUTTON_Y,
        )
        button_left = (width - button_width) // 2
        g.draw_rectangle(
            button_left,
            button_top,
            button_width,
            button_height,
            YELLOW,
        )
        button_text = 'PRESS ENTER TO SAVE SCORE'
        button_x, button_y, button_scale, button_spacing = (
            text_box_layout(
                button_text,
                button_left,
                button_top,
                button_width,
                button_height,
                normal_scale,
                padding_x,
                padding_y,
            )
        )
        g.draw_text(
            button_text,
            button_x,
            button_y,
            BLACK,
            scale=button_scale,
            spacing=button_spacing,
        )
        self._line(
            'BACKSPACE TO EDIT   ESC TO SKIP SAVING',
            responsive_px(width, height, 482),
        )
        if self.message:
            self._line(
                self.message[:60],
                responsive_px(width, height, 530),
                YELLOW,
            )

        g.refresh()
        return self.state

    def _line(
        self,
        text: str,
        center_y: int,
        color: int = WHITE,
        scale: int = NORMAL_TEXT_SCALE,
    ) -> None:
        """Center a responsive line inside a padded screen-width box."""
        width, height = self.graphics.get_window_size()
        preferred_scale = responsive_scale(
            width,
            height,
            scale,
        )
        box_x = responsive_px(width, height, 32)
        box_width = max(1, width - 2 * box_x)
        box_height = responsive_px(
            width,
            height,
            52 if scale == TITLE_TEXT_SCALE else 36,
        )
        box_y = center_y - box_height // 2
        padding_x = responsive_px(width, height, 8)
        padding_y = responsive_px(width, height, 4)
        text_x, text_y, actual_scale, spacing = text_box_layout(
            text.upper(),
            box_x,
            box_y,
            box_width,
            box_height,
            preferred_scale,
            padding_x,
            padding_y,
        )
        self.graphics.draw_text(
            text.upper(),
            text_x,
            text_y,
            color,
            scale=actual_scale,
            spacing=spacing,
        )
