"""Render a game session; simulation remains independent of MLX."""
import math
import time
from typing import TYPE_CHECKING, Callable

from ..models import AppState, Directions
from ..parsing import Config
from .events import Event, EventType
from .graphics import Graphics
from .layout import (
    BLACK,
    BLUE,
    COLOR_42,
    CYAN,
    DARK_ORANGE,
    GAME_BACKGROUND,
    GOLD,
    GRAY,
    GREEN,
    LIGHT_GREEN,
    LIGHT_ORANGE,
    LIGHT_PINK,
    LIGHT_RED,
    PAUSE_BACKGROUND,
    PINK,
    WALLS_COLOR,
    WHITE,
    YELLOW,
    fit_text_group_scale,
    percent_rect,
    text_box_layout,
    text_pixel_width,
)
from .screen_base import Screen

HUD_HEIGHT_PERCENT = 10.0
MAZE_MARGIN_PERCENT = 2.5

if TYPE_CHECKING:
    from ..session import GameSession


class GameScreen(Screen):
    """Translate controls and render the shared session, including pause."""

    def __init__(
        self,
        graphics: Graphics,
        config: Config,
        *,
        session: 'GameSession | None' = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Inject a session and clock for deterministic headless tests."""
        if session is None:
            from ..session import GameSession

            session = GameSession(config)
        self.session = session
        self.graphics = graphics
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

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
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

    def _text(
        self,
        text: str,
        yp: float,
        heightp: float,
        color: int = WHITE,
    ) -> None:
        """Draw centered text fitted to a percentage-based screen box."""
        width, height = self.graphics.get_window_size()
        box = percent_rect(
            width,
            height,
            3,
            yp,
            94,
            heightp,
        )
        text_x, text_y, scale, spacing = text_box_layout(
            text.upper(),
            *box,
            padding_xp=3,
            padding_yp=15,
        )
        self.graphics.draw_text(
            text.upper(),
            text_x,
            text_y,
            color,
            scale=scale,
            spacing=spacing,
        )

    def _colored_row(
        self,
        parts: tuple[tuple[str, int], ...],
        box_x: int,
        box_y: int,
        box_width: int,
        box_height: int,
        scale: int,
    ) -> None:
        """Draw colored text parts as one centered fitted row."""
        full_text = ''.join(text for text, _ in parts)
        text_x, text_y, actual_scale, spacing = text_box_layout(
            full_text,
            box_x,
            box_y,
            box_width,
            box_height,
            padding_xp=1,
            padding_yp=10,
            scale=scale,
        )
        x = text_x

        for index, (text, color) in enumerate(parts):
            self.graphics.draw_text(
                text,
                x,
                text_y,
                color,
                scale=actual_scale,
                spacing=spacing,
                layer='actors',
            )
            x += text_pixel_width(text, actual_scale, spacing)
            if index < len(parts) - 1:
                x += spacing

    def render(self) -> AppState:
        """Cache the maze and draw pellets, sprites, HUD, and pause overlay."""
        g = self.graphics
        s = self.session
        if s.state == AppState.ERROR:
            g.set_layer_order(['main'])
            g.fill(BLACK)
            self._text(
                'MAZE GENERATION FAILED',
                10,
                10,
                YELLOW,
            )
            self._text(s.error[:60], 22, 7)
            self._text('ENTER / ESC - MAIN MENU', 31, 7)
            g.refresh()
            return s.state

        maze = s.maze
        if maze is None:
            return AppState.ERROR

        width, height = g.get_window_size()
        hud_height = max(
            2,
            int(round(height * HUD_HEIGHT_PERCENT / 100)),
        )
        maze_margin = max(
            1,
            int(
                round(
                    min(width, height)
                    * MAZE_MARGIN_PERCENT
                    / 100
                )
            ),
        )
        maze_height = height - hud_height - 2 * maze_margin
        maze_width = width - 2 * maze_margin
        cell = max(
            1,
            min(
                maze_width // maze.width,
                maze_height // maze.height,
            ),
        )
        left = (width - cell * maze.width) // 2
        top = (
            hud_height
            + maze_margin
            + (maze_height - cell * maze.height) // 2
        )

        if self._maze_cached is not maze:
            g.create_layer('maze')
            g.create_layer('actors')
            g.fill(GAME_BACKGROUND, layer='maze')
            thickness = max(1, cell // 10)
            for y, row in enumerate(maze.cells):
                for x, walls in enumerate(row):
                    px = left + x * cell
                    py = top + y * cell
                    if walls == 15:
                        g.draw_rectangle(
                            px,
                            py,
                            cell,
                            cell,
                            COLOR_42,
                            layer='maze',
                        )
                        continue
                    for bit, dx, dy, wall_width, wall_height in (
                        (1, 0, 0, cell, thickness),
                        (2, cell - thickness, 0, thickness, cell),
                        (4, 0, cell - thickness, cell, thickness),
                        (8, 0, 0, thickness, cell),
                    ):
                        if walls & bit:
                            g.draw_rectangle(
                                px + dx,
                                py + dy,
                                wall_width,
                                wall_height,
                                WALLS_COLOR,
                                layer='maze',
                            )
            self._maze_cached = maze

        g.set_layer_order(['maze', 'actors'])
        g.clear('actors')
        for collection, radius in (
            (s.pellets, max(1, cell // 12)),
            (s.power_pellets, max(2, cell // 5)),
        ):
            for x, y in collection:
                g.draw_circle(
                    left + x * cell + cell // 2,
                    top + y * cell + cell // 2,
                    radius,
                    PINK,
                    layer='actors',
                )

        sprites = [(s.player, YELLOW)]
        for ghost, color in zip(
            s.ghosts,
            (
                LIGHT_RED,
                LIGHT_PINK,
                CYAN,
                LIGHT_ORANGE,
            ),
        ):
            if ghost.respawn_remaining <= 0:
                sprites.append(
                    (
                        ghost,
                        BLUE if s.power_remaining > 0 else color,
                    )
                )
        for actor, color in sprites:
            g.draw_circle(
                round(left + (actor.x + .5) * cell),
                round(top + (actor.y + .5) * cell),
                max(2, cell // 3),
                color,
                layer='actors',
            )

        hud_parts = (
            ('SCORE: ', GOLD),
            (str(s.score), YELLOW),
            ('  LIVES: ', LIGHT_GREEN),
            (str(s.lives), GREEN),
            ('  LEVEL: ', LIGHT_PINK),
            (str(s.level_index + 1), PINK),
            ('  TIME: ', LIGHT_ORANGE),
            (str(math.ceil(s.time_remaining)), DARK_ORANGE),
        )

        status_parts: tuple[tuple[str, int], ...]
        if s.cheat_enabled:
            status_parts = (
                ('CHEATS ', WHITE),
                ('I: ', WHITE),
                (str(int(s.invincible)), LIGHT_GREEN),
                ('  F: ', WHITE),
                (str(int(s.ghosts_frozen)), LIGHT_GREEN),
                ('  N: ', WHITE),
                ('SKIP', YELLOW),
                ('  L: ', WHITE),
                ('LIFE', LIGHT_GREEN),
                ('  B: ', WHITE),
                ('SPEED', CYAN),
                ('  V: ', WHITE),
                ('POWER', BLUE),
            )
        else:
            status_parts = (
                ('ESC/P: ', LIGHT_ORANGE),
                ('PAUSE', GRAY),
                ('   C: ', YELLOW),
                ('CHEATS', GRAY),
            )

        hud_x = maze_margin
        hud_width = max(1, width - 2 * maze_margin)
        first_row_height = max(1, hud_height // 2)
        second_row_height = max(1, hud_height - first_row_height)
        hud_text = ''.join(text for text, _ in hud_parts)
        status_text = ''.join(text for text, _ in status_parts)
        hud_scale = fit_text_group_scale(
            (hud_text, status_text),
            hud_width,
            min(first_row_height, second_row_height),
            padding_xp=1,
            padding_yp=10,
        )
        self._colored_row(
            hud_parts,
            hud_x,
            0,
            hud_width,
            first_row_height,
            hud_scale,
        )
        self._colored_row(
            status_parts,
            hud_x,
            first_row_height,
            hud_width,
            second_row_height,
            hud_scale,
        )

        if s.state == AppState.PAUSE:
            pause_box = percent_rect(
                width,
                height,
                25,
                33,
                50,
                34,
            )
            pause_x, pause_y, pause_width, pause_height = pause_box
            g.draw_rectangle(
                *pause_box,
                PAUSE_BACKGROUND,
                layer='actors',
            )
            row_height = max(1, pause_height // 2)
            pause_scale = fit_text_group_scale(
                ('> RESUME', '> MAIN MENU'),
                pause_width,
                row_height,
                padding_xp=8,
                padding_yp=15,
            )

            for index, label in enumerate(('RESUME', 'MAIN MENU')):
                text = (
                    ('> ' if index == self._pause_selected else '  ')
                    + label
                )
                row_y = pause_y + index * row_height
                text_x, text_y, actual_scale, spacing = (
                    text_box_layout(
                        text,
                        pause_x,
                        row_y,
                        pause_width,
                        row_height,
                        padding_xp=8,
                        padding_yp=15,
                        scale=pause_scale,
                    )
                )
                g.draw_text(
                    text,
                    text_x,
                    text_y,
                    YELLOW,
                    scale=actual_scale,
                    spacing=spacing,
                    layer='actors',
                )

        g.refresh()
        return s.state
