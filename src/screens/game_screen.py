"""Render a game session; simulation remains independent of MLX."""
import math
import time
from typing import TYPE_CHECKING, Callable

from .screen import Screen
from ..colors import BLACK, BLUE, PINK, WHITE, YELLOW
from ..events import Event, EventType
from ..graphics import Graphics
from ..models import AppState, Directions
from ..parsing import Config
from ..ui import NORMAL_TEXT_SCALE, TITLE_TEXT_SCALE, HUD_TEXT_SCALE

HUD_HEIGHT = 80
MAZE_MARGIN = 20

if TYPE_CHECKING:
    from ..session import GameSession


class GameScreen(Screen):
    """Translate controls and render the shared session, including pause."""

    def __init__(self, graphics: Graphics, config: Config, *,
                 session: 'GameSession | None' = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        """Inject a session and clock for deterministic headless tests."""
        if session is None:
            from ..session import GameSession
            session = GameSession(config)
        self.session = session
        self.graphics = graphics
        self.config = config
        self.clock = clock
        self._last_update = clock()
        self._pause_selected = 0
        self._maze_cached: object = None

    def new_game(self) -> None:
        """Reset all run state rather than incrementing an old level."""
        self.session.new_game()
        self._last_update = self.clock()
        self._pause_selected = 0
        self._maze_cached = None

    def next_level(self) -> None:
        """Advance only after a completed level, preserving score/lives."""
        self.session.next_level()
        self._last_update = self.clock()
        self._maze_cached = None

    def handle_event(self, event: Event) -> AppState:
        """Queue turns, pause/resume, or apply gated evaluation cheats."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if self.session.state == AppState.ERROR:
            if event.type in (EventType.KEY_ESC, EventType.KEY_ENTER):
                return AppState.MAIN_MENU
            return AppState.ERROR
        if self.session.state == AppState.PAUSE:
            if event.type in (EventType.KEY_UP, EventType.KEY_DOWN):
                self._pause_selected = 1 - self._pause_selected
            if event.type == EventType.KEY_ENTER:
                if self._pause_selected:
                    return AppState.MAIN_MENU
                self.session.toggle_pause()
            elif event.type in (EventType.KEY_ESC, EventType.KEY_PAUSE):
                self.session.toggle_pause()
            self._last_update = self.clock()
            return self.session.state
        if event.type in (EventType.KEY_ESC, EventType.KEY_PAUSE):
            self._pause_selected = 0
            self.session.toggle_pause()
            self._last_update = self.clock()
        directions = {
            EventType.KEY_UP: Directions.UP,
            EventType.KEY_DOWN: Directions.DOWN,
            EventType.KEY_LEFT: Directions.LEFT,
            EventType.KEY_RIGHT: Directions.RIGHT,
        }
        if event.type in directions:
            self.session.set_direction(directions[event.type])
        if event.type == EventType.KEY_CHEAT:
            self.session.cheat_enabled = not self.session.cheat_enabled
            if not self.session.cheat_enabled:
                self.session.invincible = False
                self.session.ghosts_frozen = False
                self.session.speed_multiplier = 1.0
        cheats = {
            EventType.KEY_INVINCIBLE: 'invincible',
            EventType.KEY_SKIP: 'skip',
            EventType.KEY_FREEZE: 'freeze',
            EventType.KEY_LIFE: 'life',
            EventType.KEY_SPEED: 'speed',
            EventType.KEY_POWER: 'power',
        }
        if event.type in cheats:
            self.session.cheat(cheats[event.type])
        return self.session.state

    def update(self) -> AppState:
        """Advance by monotonic elapsed seconds; paused simulation is inert."""
        now = self.clock()
        self.session.update(max(0.0, now - self._last_update))
        self._last_update = now
        return self.session.state

    def _text(self, text: str, y: int, color: int = WHITE,
              scale: int = NORMAL_TEXT_SCALE) -> None:
        """Draw centered text using a fixed font size."""
        width, _ = self.graphics.get_window_size()
        self.graphics.draw_text(text.upper(),
                                max(8, (width - len(text) * 6 * scale) // 2),
                                y, color, scale=scale, spacing=scale)

    def render(self) -> AppState:
        """Cache the maze and draw pellets, sprites, HUD, and pause overlay."""
        g = self.graphics
        s = self.session
        if s.state == AppState.ERROR:
            g.set_layer_order(['main'])
            g.fill(BLACK)
            self._text('MAZE GENERATION FAILED', 100, YELLOW, TITLE_TEXT_SCALE)
            self._text(s.error[:60], 160)
            self._text('ENTER / ESC - MAIN MENU', 220)
            g.refresh()
            return s.state
        maze = s.maze
        if maze is None:
            return AppState.ERROR
        width, height = g.get_window_size()
        maze_height = height - HUD_HEIGHT - 2 * MAZE_MARGIN
        cell = max(1, min((width - 2 * MAZE_MARGIN) // maze.width,
                          maze_height // maze.height))
        left = (width - cell * maze.width) // 2
        top = (HUD_HEIGHT + MAZE_MARGIN
               + (maze_height - cell * maze.height) // 2)
        if self._maze_cached is not maze:
            g.create_layer('maze')
            g.create_layer('actors')
            g.fill(BLACK, layer='maze')
            thickness = max(1, cell // 10)
            for y, row in enumerate(maze.cells):
                for x, walls in enumerate(row):
                    px, py = left + x * cell, top + y * cell
                    if walls == 15:
                        g.draw_rectangle(px, py, cell, cell, BLUE,
                                         layer='maze')
                        continue
                    for bit, dx, dy, w, h in (
                            (1, 0, 0, cell, thickness),
                            (2, cell - thickness, 0, thickness, cell),
                            (4, 0, cell - thickness, cell, thickness),
                            (8, 0, 0, thickness, cell)):
                        if walls & bit:
                            g.draw_rectangle(px + dx, py + dy, w, h,
                                             BLUE, layer='maze')
            self._maze_cached = maze
        g.set_layer_order(['maze', 'actors'])
        g.clear('actors')
        for collection, radius in ((s.pellets, max(1, cell // 12)),
                                   (s.power_pellets, max(2, cell // 5))):
            for x, y in collection:
                g.draw_circle(left + x * cell + cell // 2,
                              top + y * cell + cell // 2, radius, PINK,
                              layer='actors')
        sprites = [(s.player, YELLOW)]
        for ghost, color in zip(s.ghosts,
                                (0xFFFF4444, 0xFFFF99CC,
                                 0xFF44FFFF, 0xFFFFAA44)):
            if ghost.respawn_remaining <= 0:
                sprites.append((ghost, BLUE if s.power_remaining > 0
                                else color))
        for actor, color in sprites:
            g.draw_circle(round(left + (actor.x + .5) * cell),
                          round(top + (actor.y + .5) * cell),
                          max(2, cell // 3), color, layer='actors')
        hud = (f'SCORE {s.score}   LIVES {s.lives}   '
               f'LEVEL {s.level_index + 1}   '
               f'TIME {math.ceil(s.time_remaining)}')
        scale = HUD_TEXT_SCALE
        g.draw_text(hud, 10, 12, WHITE, scale=scale, spacing=scale,
                    layer='actors')
        status = 'ESC/P PAUSE   C CHEATS'
        if s.cheat_enabled:
            status = (f'CHEATS I:{int(s.invincible)} F:{int(s.ghosts_frozen)} '
                      'N:SKIP L:LIFE B:SPEED V:POWER')
        g.draw_text(status, 10, 48, YELLOW, scale=HUD_TEXT_SCALE,
                    spacing=HUD_TEXT_SCALE, layer='actors')
        if s.state == AppState.PAUSE:
            g.draw_rectangle(width // 4, height // 3, width // 2,
                             height // 3, BLACK, layer='actors')
            for i, label in enumerate(('RESUME', 'MAIN MENU')):
                g.draw_text(('> ' if i == self._pause_selected else '  ')
                            + label, width // 3, height // 3 + 40 + i * 40,
                            YELLOW, scale=NORMAL_TEXT_SCALE,
                            spacing=NORMAL_TEXT_SCALE, layer='actors')
        g.refresh()
        return s.state
