"""Victory/loss score presentation and keyboard player-name entry."""
from .screen import Screen
from ..colors import BLACK, WHITE, YELLOW
from ..events import Event, EventType
from ..graphics import Graphics
from ..highscores import HighscoreStore
from ..models import AppState


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
        width, height = g.get_window_size()
        g.set_layer_order(['main'])
        g.fill(BLACK)
        self._line('VICTORY - CONGRATULATIONS'
                   if self.state == AppState.VICTORY else 'GAME OVER',
                   height * 12 // 100, YELLOW)
        self._line(f'FINAL SCORE {self.score}', height * 24 // 100)
        self._line('TYPE ON YOUR KEYBOARD TO ENTER YOUR NAME',
                   height * 36 // 100)
        self._line('SAVE FAILED - ENTER TO RETRY' if self.message
                   else 'MAX 10: LETTERS / DIGITS / SPACES',
                   height * 43 // 100, YELLOW)

        box_width = width * 3 // 4
        box_height = max(32, min(80, height // 9))
        left, top = (width - box_width) // 2, height // 2
        g.draw_rectangle(left, top, box_width, box_height, YELLOW)
        g.draw_rectangle(left + 2, top + 2, box_width - 4,
                         box_height - 4, 0xFF18243B)
        text = self.name.upper() if self.name else 'TYPE YOUR NAME HERE'
        scale = max(1, min(3, (box_width - 24) // (len(text) * 6),
                           (box_height - 8) // 8))
        text_x = (width - len(text) * 6 * scale) // 2
        text_y = top + (box_height - 8 * scale) // 2
        g.draw_text(text, text_x, text_y, WHITE,
                    scale=scale, spacing=scale)
        if self.name and not self._added:
            g.draw_rectangle(text_x + len(text) * 6 * scale + 2,
                             text_y, 2, 8 * scale, YELLOW)

        button_width = width * 4 // 5
        button_height = max(24, min(64, height // 12))
        button_top = height * 72 // 100
        g.draw_rectangle((width - button_width) // 2, button_top,
                         button_width, button_height, YELLOW)
        self._line('PRESS ENTER TO SAVE SCORE',
                   button_top + button_height // 2, BLACK,
                   max_scale=max(1, (button_height - 8) // 8))
        self._line('BACKSPACE TO EDIT   ESC TO SKIP SAVING',
                   height * 88 // 100)
        if self.message:
            limit = max(1, (width - 40) // 6)
            self._line(self.message[:limit], height * 95 // 100, YELLOW,
                       max_scale=1)
        g.refresh()
        return self.state

    def _line(self, text: str, center_y: int, color: int = WHITE,
              max_scale: int = 3) -> None:
        """Center a readable bitmap line within the native window bounds."""
        width, _ = self.graphics.get_window_size()
        scale = max(1, min(max_scale, 3,
                           (width - 40) // max(1, len(text) * 6)))
        self.graphics.draw_text(text.upper(),
                                (width - len(text) * 6 * scale) // 2,
                                center_y - 4 * scale, color,
                                scale=scale, spacing=scale)
