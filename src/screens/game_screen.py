from mazegenerator import MazeGenerator
from .screen import Screen
from ..models import AppState, Directions
from ..graphics import Graphics
from ..parsing import Config
from ..colors import WHITE, YELLOW, GREEN, BLACK, ORANGE
from ..events import Event, EventType
from ..ui import Layout, AbsoluteRect, AbsoluteCircle
from ..game import PacMan
import random
import math

TWO_BASE_TABLE = {
    0: [0, 0, 0, 0],
    1: [0, 0, 0, 1],
    2: [0, 0, 1, 0],
    3: [0, 0, 1, 1],
    4: [0, 1, 0, 0],
    5: [0, 1, 0, 1],
    6: [0, 1, 1, 0],
    7: [0, 1, 1, 1],
    8: [1, 0, 0, 0],
    9: [1, 0, 0, 1],
    10: [1, 0, 1, 0],
    11: [1, 0, 1, 1],
    12: [1, 1, 0, 0],
    13: [1, 1, 0, 1],
    14: [1, 1, 1, 0],
    15: [1, 1, 1, 1],
}

PACGUM_COLOR = GREEN
SUPER_PACGUM_COLOR = GREEN
BORDER_COLOR = GREEN
PACMAN_COLOR = ORANGE

CELL_PREFIX = "CELL_"
BORDER_PREFIX = "BORDER_"
PACGUM_PREFIX = "PACGUM_"
SUPER_PACGUM_PREFIX = "SUPER_PACGUM_"

BORDER_SIZE = 0.2
MARGIN_X = 2
MARGIN_Y = 2
TOPBAR_HEIGHT = 10

PACMAN_SPAWN_COL = 1
PACMAN_SPAWN_ROW = 1
PACMAN_SPEED = 4

LAYER_MAZE = "maze"
LAYER_PACGUMS = "pacgums"
LAYER_SPRITES = "sprites"
LAYER_ORDER = [LAYER_MAZE, LAYER_PACGUMS, LAYER_SPRITES]

# Which wall a given movement direction needs clear to be taken.
DIRECTION_TO_WALL_KEY = {
    Directions.LEFT: "west",
    Directions.RIGHT: "east",
    Directions.UP: "north",
    Directions.DOWN: "south",
}


class GameScreen(Screen):

    """Gameplay screen."""

    def __init__(self, graphics: Graphics, config: Config) -> None:
        self.LEVEL = 0
        self._self_app_state = AppState.GAME

        self.graphics = graphics
        self.config = config

        self.layout = Layout()
        self._maze_gen = MazeGenerator()

        # Grid-based pacman state. Real x/y/cell_size are set in
        # _spawn_pacman() once the maze geometry is known.
        self._width, self._height = self.graphics.get_window_size()
        self._pacman_col = PACMAN_SPAWN_COL
        self._pacman_row = PACMAN_SPAWN_ROW
        self._to_visual_x = 100
        self._to_visual_y = 100

        # self.layout.add_circle(50, 50, 10, "AAA")
        # abs_circle = self.layout.get_circle_absolute(
        #    "AAA", self._width, self._height)
        # print(abs_circle.x, abs_circle.y)
        # print(abs_circle.contains(1000, 600))
        # return
        self._start_level()

    def _start_level(self) -> None:
        self._cell_names: list[str] = []
        self._border_names: list[str] = []
        self._pacgum_names: list[str] = []
        self._super_pacgum_names: list[str] = []
        self._42_pattern: list[str] = []
        self._cell_walls: dict[tuple[int, int], dict[str, bool]] = {}

        self._ensure_layers()

        # Absolute geometry cache.
        #
        # The Layout stores positions in percentages. These values are
        # converted to pixels only when the window size changes.
        self._cache_width = self._width
        self._cache_height = self._height

        self._cell_cache: dict[str, AbsoluteRect] = {}
        self._border_cache: dict[str, AbsoluteRect] = {}
        self._pacgum_cache: dict[str, AbsoluteCircle] = {}
        self._super_pacgum_cache: dict[str, AbsoluteCircle] = {}

        self._make_maze()
        self._make_pacgums()
        self._rebuild_cache()
        self._spawn_pacman(PACMAN_SPAWN_COL, PACMAN_SPAWN_ROW)

    def handle_event(self, event: Event) -> AppState:
        # return self._self_app_state
        """Handle input events."""
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_ESC:
            return AppState.EXIT
        if event.type == EventType.KEY_UP:
            self._pac_man.set_direction(Directions.UP)
            return self._self_app_state
        if event.type == EventType.KEY_RIGHT:
            self._pac_man.set_direction(Directions.RIGHT)
            return self._self_app_state
        if event.type == EventType.KEY_DOWN:
            self._pac_man.set_direction(Directions.DOWN)
            return self._self_app_state
        if event.type == EventType.KEY_LEFT:
            self._pac_man.set_direction(Directions.LEFT)
            return self._self_app_state
        return self._self_app_state

    def update(self) -> AppState:
        """Update gameplay logic."""
        # return self._self_app_state
        departed = self._pac_man.move(self._can_move, self._eat_pacgum)
        if departed is not None:
            dcol, drow = departed.value
            self._pacman_col += dcol
            self._pacman_row += drow
        return self._self_app_state

    def render(self) -> AppState:
        """Render the current frame."""
        # return self._self_app_state
        # The maze and pacgums layers are drawn once in _rebuild_cache()
        # and never cleared here - they act as the cache. Only the
        # sprites layer (pacman, later ghosts) is redrawn every frame.
        self.graphics.clear(LAYER_SPRITES)
        self._render_pacman()
        self.graphics.visualise_dot(
            self._to_visual_x,
            self._to_visual_y,
            layer=LAYER_SPRITES)
        self.graphics.refresh()

        return self._self_app_state

    # ------------------------------------------------------------------
    # Layers
    # ------------------------------------------------------------------

    def _ensure_layers(self) -> None:
        """Create the layers if this is the first time, otherwise wipe
        the layers whose content depends on the (re)generated maze."""
        first_time = not self.graphics.has_layer(LAYER_MAZE)

        for name in LAYER_ORDER:
            if not self.graphics.has_layer(name):
                self.graphics.create_layer(name)

        if first_time:
            self.graphics.set_layer_order(LAYER_ORDER)
        else:
            # Level restart / new level: wipe the static layers so the
            # old maze/pacgums don't bleed into the new one.
            self.graphics.clear(LAYER_MAZE)
            self.graphics.clear(LAYER_PACGUMS)

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _rebuild_cache(self) -> None:
        """Rebuild all pixel-based geometry caches and draw the static
        layers (maze walls/cells, pacgums) exactly once."""
        self._cache_width = self._width
        self._cache_height = self._height

        self._cell_cache.clear()
        self._border_cache.clear()
        self._pacgum_cache.clear()
        self._super_pacgum_cache.clear()

        self._cache_cells()
        self._cache_borders()
        self._cache_pacgums()

        # Opaque base fill so the maze layer covers every pixel of the
        # window (including margins/corridors), otherwise it can't fully
        # overwrite whatever was drawn on top of it the previous frame.
        self.graphics.fill(BLACK, layer=LAYER_MAZE)
        self._render_cells()
        self._render_borders()
        self._render_pacgums()

    def _cache_cells(self) -> None:
        """Cache all maze cells in absolute pixel coordinates."""
        for name in self._cell_names:
            rect = self.layout.get_rect_absolute(
                name,
                self._width,
                self._height,
            )

            if rect is not None:
                self._cell_cache[name] = rect

    def _cache_borders(self) -> None:
        """Cache all maze borders in absolute pixel coordinates."""
        for name in self._border_names:
            rect = self.layout.get_rect_absolute(
                name,
                self._width,
                self._height,
            )

            if rect is not None:
                self._border_cache[name] = rect

    def _cache_pacgums(self) -> None:
        """Cache the pixel position and radius of all pac-gums."""
        for pacgum_name in self._pacgum_names:
            abs_circle = self.layout.get_circle_absolute(
                pacgum_name, self._width, self._height)
            if abs_circle is None:
                continue
            abs_circle.color = PACGUM_COLOR
            self._pacgum_cache[pacgum_name] = abs_circle
        for super_pacgum_name in self._super_pacgum_names:
            abs_circle = self.layout.get_circle_absolute(
                super_pacgum_name, self._width, self._height)
            if abs_circle is None:
                continue
            abs_circle.color = PACGUM_COLOR
            self._super_pacgum_cache[super_pacgum_name] = abs_circle

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_cells(self) -> None:
        """Render maze cells using cached absolute geometry."""
        for index, name in enumerate(self._cell_names):
            cell = self._cell_cache.get(name)

            if cell is None:
                continue

            color = WHITE if index % 2 == 0 else YELLOW

            self.graphics.draw_rectangle(
                x=cell.x,
                y=cell.y,
                width=cell.width,
                height=cell.height,
                color=color,
                layer=LAYER_MAZE,
            )

    def _render_borders(self) -> None:
        """Render maze walls using cached absolute geometry."""
        for name in self._border_names:
            border = self._border_cache.get(name)

            if border is None:
                continue

            self.graphics.draw_rectangle(
                x=border.x,
                y=border.y,
                width=border.width,
                height=border.height,
                color=BORDER_COLOR,
                layer=LAYER_MAZE,
            )

    def _render_pacgums(self) -> None:
        """Render all remaining pac-gums."""
        for pacgum_name in self._pacgum_names:
            pacgum = self._pacgum_cache[pacgum_name]
            self.graphics.draw_circle(
                pacgum.x, pacgum.y, pacgum.radius, PACGUM_COLOR,
                layer=LAYER_PACGUMS,
            )
        for super_pacgum_name in self._super_pacgum_names:
            super_pacgum = self._super_pacgum_cache[super_pacgum_name]
            self.graphics.draw_circle(
                super_pacgum.x, super_pacgum.y,
                super_pacgum.radius, PACGUM_COLOR,
                layer=LAYER_PACGUMS,
            )

    def _render_pacman(self) -> None:
        self.graphics.draw_image(x=self._pac_man.x,
                                 y=self._pac_man.y,
                                 bits=list(self._pac_man.bit_map),
                                 line_len=self._pac_man.size,
                                 color=PACMAN_COLOR,
                                 layer=LAYER_SPRITES)

    # ------------------------------------------------------------------
    # Maze
    # ------------------------------------------------------------------

    def _make_maze(self) -> None:
        """Generate the maze and create its percentage-based layout."""
        lvl = self.config.levels[self.LEVEL]

        self._maze_gen.generate()

        total_width = 100 - MARGIN_X * 2
        total_height = 100 - MARGIN_Y * 2

        maze_width = total_width
        maze_height = total_height - TOPBAR_HEIGHT

        # Available size of one cell in pixels.
        cell_width = maze_width / lvl.width / 100 * self._width
        cell_height = maze_height / lvl.height / 100 * self._height

        # Keep cells square.
        cell_size = min(cell_width, cell_height)
        self._cell_size_px = int(math.ceil(cell_size))

        cell_width_p = cell_size / self._width * 100
        cell_height_p = cell_size / self._height * 100

        final_maze_width = cell_width_p * lvl.width
        final_maze_height = cell_height_p * lvl.height

        final_total_width = final_maze_width
        final_total_height = final_maze_height + TOPBAR_HEIGHT

        margin_left = (100 - final_total_width) / 2
        margin_top = (100 - final_total_height) / 2

        maze_top = margin_top + TOPBAR_HEIGHT

        for y, row in enumerate(self._maze_gen.maze):
            y_pos = maze_top + cell_height_p * y

            for x, cell_bits in enumerate(row):
                x_pos = margin_left + cell_width_p * x
                cell_name = f"{CELL_PREFIX}{x}_{y}"
                self.layout.add_rect(
                    xp=x_pos,
                    yp=y_pos,
                    widthp=cell_width_p,
                    heightp=cell_height_p,
                    name=cell_name,
                )
                self._cell_names.append(cell_name)

                west, south, east, north = TWO_BASE_TABLE[cell_bits]
                self._cell_walls[(x, y)] = {
                    "west": bool(west),
                    "south": bool(south),
                    "east": bool(east),
                    "north": bool(north),
                }

                self._make_borders(
                    cell_name,
                    cell_bits,
                )

    def _make_borders(self, name: str, bits: int) -> None:
        """Create percentage-based wall rectangles for a maze cell."""
        cell = self.layout.get_rect(name)
        if cell is None:
            return

        west, south, east, north = TWO_BASE_TABLE[bits]
        border_x_thickness = cell.widthp * BORDER_SIZE
        border_y_thickness = cell.heightp * BORDER_SIZE

        if west:
            border_name = f"{BORDER_PREFIX}{name}_WEST"

            self.layout.add_rect(
                xp=cell.xp - border_x_thickness / 2,
                yp=cell.yp - border_y_thickness / 2,
                widthp=border_x_thickness,
                heightp=cell.heightp + border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if south:
            border_name = f"{BORDER_PREFIX}{name}_SOUTH"

            self.layout.add_rect(
                xp=cell.xp - border_x_thickness / 2,
                yp=cell.yp + cell.heightp - border_y_thickness / 2,
                widthp=cell.widthp + border_x_thickness,
                heightp=border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if east:
            border_name = f"{BORDER_PREFIX}{name}_EAST"

            self.layout.add_rect(
                xp=cell.xp + cell.widthp - border_x_thickness / 2,
                yp=cell.yp - border_y_thickness / 2,
                widthp=border_x_thickness,
                heightp=cell.heightp + border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if north:
            border_name = f"{BORDER_PREFIX}{name}_NORTH"

            self.layout.add_rect(
                xp=cell.xp - border_x_thickness / 2,
                yp=cell.yp - border_y_thickness / 2,
                widthp=cell.widthp + border_x_thickness,
                heightp=border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if west and south and east and north:
            self._42_pattern.append(name)

    # ------------------------------------------------------------------
    # Pac-gums
    # ------------------------------------------------------------------

    def _make_pacgums(self) -> None:
        """Create the initial pac-gum distribution."""
        lvl = self.config.levels[self.LEVEL]

        corners = {
            0,                  # top-left
            lvl.width - 1,           # top-right
            (lvl.height - 1) * lvl.width,  # bottom-left
            lvl.width * lvl.height - 1     # bottom-right
        }
        available = [x for i, x in enumerate(
            self._cell_names) if i not in corners and
            self._cell_names[i] not in self._42_pattern]
        selected_cell_names = random.sample(available, self.config.pacgum)
        for cell_name in selected_cell_names:
            cell = self.layout.get_rect(cell_name)
            if cell is None:
                return
            pacgum_name = f"{PACGUM_PREFIX}{cell_name}"
            self.layout.add_circle(cell.xp + cell.widthp / 2,
                                   cell.yp + cell.heightp / 2,
                                   cell.widthp / 4,
                                   pacgum_name,
                                   )
            self._pacgum_names.append(pacgum_name)
        for corner in corners:
            cell = self.layout.get_rect(self._cell_names[corner])
            if cell is None:
                return
            super_pacgum_name = f"{SUPER_PACGUM_PREFIX}{corner}"
            self.layout.add_circle(cell.xp + cell.widthp / 2,
                                   cell.yp + cell.heightp / 2,
                                   cell.widthp / 2,
                                   super_pacgum_name,
                                   )
            self._super_pacgum_names.append(super_pacgum_name)

    def _eat_pacgum(self, x: int, y: int) -> None:
        # print(f"trying for:({x},{y})")
        self._to_visual_x = x
        self._to_visual_y = y
        i = 0
        for pacgum_name in self._pacgum_names:
            abs_circle = self._pacgum_cache[pacgum_name]
            if abs_circle.contains(x, y):
                print("EATEN")
                del self._pacgum_cache[pacgum_name]
                del self._pacgum_names[i]
                self.graphics.clear(LAYER_PACGUMS)
                self._render_pacgums()
            i += 1

    # ------------------------------------------------------------------
    # Pac-Man
    # ------------------------------------------------------------------

    def _can_move(self, direction: Directions) -> bool:
        """Whether pacman can leave its current logical cell in `direction`."""
        if direction == Directions.STOP:
            return False
        walls = self._cell_walls.get((self._pacman_col, self._pacman_row))
        if walls is None:
            return False
        wall_key = DIRECTION_TO_WALL_KEY[direction]
        return not walls[wall_key]

    def _spawn_pacman(self, col: int, row: int) -> None:
        """Place pacman at rest, centered on the given maze cell."""
        cell = self._cell_cache.get(f"{CELL_PREFIX}{col}_{row}")
        if cell is None:
            return

        sprite_size = int(
            math.ceil(self._cell_size_px * (0.9 - BORDER_SIZE)))
        center_x = cell.x + cell.width // 2 - sprite_size // 2
        center_y = cell.y + cell.height // 2 - sprite_size // 2

        self._pac_man = PacMan(
            x=center_x,
            y=center_y,
            cell_size=self._cell_size_px,
            size=sprite_size,
            speed=PACMAN_SPEED
        )

        self._pacman_col = col
        self._pacman_row = row
