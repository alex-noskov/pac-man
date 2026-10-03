"""Victory/loss score presentation and keyboard player-name entry."""
from .screen import Screen
from ..colors import BLACK, WHITE, YELLOW
from ..events import Event, EventType
from ..graphics import Graphics
from ..highscores import HighscoreStore
from ..models import AppState
from ..ui import NORMAL_TEXT_SCALE, TITLE_TEXT_SCALE

NAME_BOX_WIDTH = 600
NAME_BOX_HEIGHT = 48
NAME_BOX_Y = 280
SAVE_BUTTON_WIDTH = 560
SAVE_BUTTON_HEIGHT = 48
SAVE_BUTTON_Y = 390


class EndScreen(Screen):
    """Display an outcome and save one score with recoverable I/O errors."""

    def __init__(self, graphics: Graphics, store: HighscoreStore,
                 state: AppState) -> None:
        """Bind shared graphics/storage to a specific win or loss screen."""
        self.graphics = graphics
        self.store = store
        self.state = state
        self.begin(0)

    def begin(self, score: int) -> None:
        """Reset editing and submission state for each completed run."""
        self.score = score
        self.name = ''
        self.message = ''
        self._added = False

    def handle_event(self, event: Event) -> AppState:
        """Edit a validated ten-character name, save, retry, or leave."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_ESC:
            return AppState.MAIN_MENU
        if event.type == EventType.TEXT and not self._added:
            text = str(event.data.get('text', ''))
            self.name = (self.name + ''.join(
                c for c in text if c.isascii() and
                (c.isalnum() or c == ' ')))[:10]
        elif event.type == EventType.KEY_BACKSPACE and not self._added:
            self.name = self.name[:-1]
        elif event.type == EventType.KEY_ENTER:
            if not self._added:
                self._added = self.store.add(self.name.strip() or 'PLAYER',
                                             self.score)
            if self._added and self.store.save():
                return AppState.MAIN_MENU
            self.message = self.store.error
        return self.state

    def update(self) -> AppState:
        """Keep the finished score and all gameplay timers frozen."""
        return self.state

    def render(self) -> AppState:
        """Present an unmistakable keyboard field and save confirmation."""
        g = self.graphics
        width, _ = g.get_window_size()
        g.set_layer_order(['main'])
        g.fill(BLACK)
        self._line('VICTORY - CONGRATULATIONS'
                   if self.state == AppState.VICTORY else 'GAME OVER',
                   70, YELLOW, scale=TITLE_TEXT_SCALE)
        self._line(f'FINAL SCORE {self.score}', 126)
        self._line('TYPE ON YOUR KEYBOARD TO ENTER YOUR NAME',
                   194)
        self._line('SAVE FAILED - ENTER TO RETRY' if self.message
                   else 'MAX 10: LETTERS / DIGITS / SPACES',
                   238, YELLOW)

        box_width, box_height = NAME_BOX_WIDTH, NAME_BOX_HEIGHT
        left, top = (width - box_width) // 2, NAME_BOX_Y
        g.draw_rectangle(left, top, box_width, box_height, YELLOW)
        g.draw_rectangle(left + 2, top + 2, box_width - 4,
                         box_height - 4, 0xFF18243B)
        text = self.name.upper() if self.name else 'TYPE YOUR NAME HERE'
        scale = NORMAL_TEXT_SCALE
        text_x = (width - len(text) * 6 * scale) // 2
        text_y = top + (box_height - 8 * scale) // 2
        g.draw_text(text, text_x, text_y, WHITE,
                    scale=scale, spacing=scale)
        if self.name and not self._added:
            g.draw_rectangle(text_x + len(text) * 6 * scale + 2,
                             text_y, 2, 8 * scale, YELLOW)

        button_width, button_height = SAVE_BUTTON_WIDTH, SAVE_BUTTON_HEIGHT
        button_top = SAVE_BUTTON_Y
        g.draw_rectangle((width - button_width) // 2, button_top,
                         button_width, button_height, YELLOW)
        self._line('PRESS ENTER TO SAVE SCORE',
                   button_top + button_height // 2, BLACK)
        self._line('BACKSPACE TO EDIT   ESC TO SKIP SAVING',
                   482)
        if self.message:
            self._line(self.message[:60], 530, YELLOW)
        g.refresh()
        return self.state

    def _line(self, text: str, center_y: int, color: int = WHITE,
              scale: int = NORMAL_TEXT_SCALE) -> None:
        """Center a line using an explicit fixed bitmap font size."""
        width, _ = self.graphics.get_window_size()
        self.graphics.draw_text(text.upper(),
                                (width - len(text) * 6 * scale) // 2,
                                center_y - 4 * scale, color,
                                scale=scale, spacing=scale)
