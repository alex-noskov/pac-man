"""Victory/loss score presentation and keyboard player-name entry."""
from ..highscores import HighscoreStore
from ..models import AppState
from .events import Event, EventType
from .graphics import Graphics
from .layout import (
    BLACK,
    WHITE,
    YELLOW,
    fit_text_group_scale,
    percent_rect,
    text_box_layout,
    text_pixel_width,
)
from .screen_base import Screen


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
        """Render percentage boxes with text fitted inside their padding."""
        g = self.graphics
        width, height = g.get_window_size()

        g.set_layer_order(['main'])
        g.fill(BLACK)

        self._line(
            'VICTORY - CONGRATULATIONS'
            if self.state == AppState.VICTORY
            else 'GAME OVER',
            5,
            4,
            90,
            10,
            YELLOW,
        )
        self._line(
            f'FINAL SCORE {self.score}',
            10,
            15,
            80,
            6,
        )
        self._line(
            'TYPE ON YOUR KEYBOARD TO ENTER YOUR NAME',
            5,
            23,
            90,
            6,
        )
        self._line(
            'SAVE FAILED - ENTER TO RETRY'
            if self.message
            else 'MAX 10: LETTERS / DIGITS / SPACES',
            5,
            29,
            90,
            6,
            YELLOW,
        )

        name_box = percent_rect(
            width,
            height,
            26.5,
            36,
            47,
            7,
        )
        left, top, box_width, box_height = name_box
        border = max(1, min(box_width, box_height) // 24)

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
            max(1, box_width - 2 * border),
            max(1, box_height - 2 * border),
            0xFF18243B,
        )

        placeholder = 'TYPE YOUR NAME HERE'
        text = self.name.upper() if self.name else placeholder
        field_scale = fit_text_group_scale(
            (placeholder, text),
            box_width,
            box_height,
            padding_xp=5,
            padding_yp=18,
        )
        text_x, text_y, _, spacing = text_box_layout(
            text,
            *name_box,
            padding_xp=5,
            padding_yp=18,
            scale=field_scale,
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
            cursor_width = border
            cursor_gap = border
            typed_width = text_pixel_width(
                text,
                field_scale,
                spacing,
            )
            g.draw_rectangle(
                text_x + typed_width + cursor_gap,
                text_y,
                cursor_width,
                8 * field_scale,
                YELLOW,
            )

        save_box = percent_rect(
            width,
            height,
            28,
            49,
            44,
            7,
        )
        g.draw_rectangle(
            *save_box,
            YELLOW,
        )
        button_text = 'PRESS ENTER TO SAVE SCORE'
        button_x, button_y, button_scale, button_spacing = (
            text_box_layout(
                button_text,
                *save_box,
                padding_xp=5,
                padding_yp=18,
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
            5,
            60,
            90,
            6,
        )
        if self.message:
            self._line(
                self.message[:60],
                5,
                67,
                90,
                6,
                YELLOW,
            )

        g.refresh()
        return self.state

    def _line(
        self,
        text: str,
        xp: float,
        yp: float,
        widthp: float,
        heightp: float,
        color: int = WHITE,
    ) -> None:
        """Draw one centered line inside a percentage-based text box."""
        width, height = self.graphics.get_window_size()
        box = percent_rect(
            width,
            height,
            xp,
            yp,
            widthp,
            heightp,
        )
        text_x, text_y, scale, spacing = text_box_layout(
            text.upper(),
            *box,
            padding_xp=4,
            padding_yp=18,
        )
        self.graphics.draw_text(
            text.upper(),
            text_x,
            text_y,
            color,
            scale=scale,
            spacing=spacing,
        )
