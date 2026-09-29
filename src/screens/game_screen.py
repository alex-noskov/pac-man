from mazegenerator import MazeGenerator
from .screen import Screen
from ..models import AppState, Directions
from ..graphics import Graphics
from ..parsing import Config
from ..colors import WHITE, YELLOW, BLACK, BLUE, PINK
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


PACGUM_COLOR = PINK
SUPER_PACGUM_COLOR = PINK
BORDER_COLOR = BLUE
PACMAN_COLOR = YELLOW


CELL_PREFIX = "CELL_"
BORDER_PREFIX = "BORDER_"
TOP_BAR_PREFIX = "TOP_BAR_"
VALUE_PREFIX = "VALUE_"
PACGUM_PREFIX = "PACGUM_"
SUPER_PACGUM_PREFIX = "SUPER_PACGUM_"


PACMAN_SPAWN_COL = 0
PACMAN_SPAWN_ROW = 0
PACMAN_SPEED = 10


LAYER_MAZE = "maze"
LAYER_PACGUMS = "pacgums"
LAYER_VALUES = "values"
LAYER_SPRITES = "sprites"

LAYER_ORDER = [
    LAYER_MAZE,
    LAYER_PACGUMS,
    LAYER_VALUES,
    LAYER_SPRITES,
]


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
        self._score = 0
        self._lives = 3
        self._level = -1

        self.BORDER_SIZE = 0.2
        self.TOPBAR_HEIGHT = 10

        self.STARTED = False

        self.graphics = graphics
        self.config = config

        # Grid-based Pac-Man state.
        # Real x/y/cell_size are set in _spawn_pacman()
        # once the maze geometry is known.
        self._width, self._height = self.graphics.get_window_size()

        self._pacman_col = PACMAN_SPAWN_COL
        self._pacman_row = PACMAN_SPAWN_ROW

        self._to_visual_x = 100
        self._to_visual_y = 100

    # ------------------------------------------------------------------
    # Screen
    # ------------------------------------------------------------------

    def _start_screen(self) -> None:
        print("START LEVEL!")
        self.MARGIN_X = 2.0
        self.MARGIN_Y = 2.0
        self._level += 1
        self._LEVEL_DICT = self.config.levels[self._level]
        self.layout = Layout()
        self._maze_gen = MazeGenerator(
            (self._LEVEL_DICT.width, self._LEVEL_DICT.height))
        self._self_app_state = AppState.GAME

        self._cell_names: list[str] = []
        self._border_names: list[str] = []
        self._top_bar_names: list[str] = []
        self._value_names: list[str] = []
        self._pacgum_names: list[str] = []
        self._super_pacgum_names: list[str] = []

        self._42_pattern: list[str] = []
        self._cell_walls: dict[tuple[int, int], dict[str, bool]] = {}

        self.graphics.clear()
        self.graphics.fill(BLACK)

        for name in LAYER_ORDER:
            self.graphics.create_layer(name)
        self.graphics.set_layer_order(LAYER_ORDER)

        # Absolute geometry cache.
        self._cell_cache: dict[str, AbsoluteRect] = {}
        self._border_cache: dict[str, AbsoluteRect] = {}
        self._top_bar_cache: dict[str, AbsoluteRect] = {}
        self._value_cache: dict[str, AbsoluteRect] = {}
        self._pacgum_cache: dict[str, AbsoluteCircle] = {}
        self._super_pacgum_cache: dict[str, AbsoluteCircle] = {}

        self._time = 0
        self._top_bar_scale = 0
        self._value_scale = 0

        self._make_maze()
        self._make_pacgums()
        self._make_top_bar()
        self._make_values()

        self._rebuild_cache()

        self._spawn_pacman(
            PACMAN_SPAWN_COL,
            PACMAN_SPAWN_ROW,
        )
        self.STARTED = True

    # def _end_state(self, return_state: AppState) -> AppState:
    #    self.STARTED = False

    #    for layer in LAYER_ORDER:
    #        self.graphics.remove_layer(layer)

    #    return return_state

    def _return_state(self, return_state: AppState) -> AppState:
        if return_state == AppState.LEVEL_COMPLETE or \
                return_state == AppState.MAIN_MENU:
            self.STARTED = False
            for layer in LAYER_ORDER:
                self.graphics.remove_layer(layer)
        return return_state

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def handle_event(self, event: Event) -> AppState:
        """Handle input events."""

        if not self.STARTED:
            self._start_screen()
        if event.type == EventType.CLOSE:
            return self._return_state(AppState.EXIT)
        if event.type == EventType.KEY_ESC:
            return self._return_state(AppState.MAIN_MENU)
        if event.type == EventType.KEY_UP:
            self._pac_man.set_direction(Directions.UP)
            return self._return_state(self._self_app_state)
        if event.type == EventType.KEY_RIGHT:
            self._pac_man.set_direction(Directions.RIGHT)
            return self._return_state(self._self_app_state)
        if event.type == EventType.KEY_DOWN:
            self._pac_man.set_direction(Directions.DOWN)
            return self._return_state(self._self_app_state)
        if event.type == EventType.KEY_LEFT:
            self._pac_man.set_direction(Directions.LEFT)
            return self._return_state(self._self_app_state)
        return self._return_state(self._self_app_state)

    def update(self) -> AppState:
        """Update gameplay logic."""

        if not self.STARTED:
            self._start_screen()
        departed = self._pac_man.move(
            self._can_move,
            self._eat_pacgum,
        )
        if departed is not None:
            dcol, drow = departed.value

            self._pacman_col += dcol
            self._pacman_row += drow
        return self._return_state(self._self_app_state)

    def render(self) -> AppState:
        """Render the current frame."""

        if not self.STARTED:
            self._start_screen()
        # Static maze/top-bar/pacgum/value layers are rendered by
        # _rebuild_cache(). Only the sprite layer is redrawn.
        self.graphics.clear(LAYER_SPRITES)
        self._render_pacman()
        # self.graphics.visualise_dot(
        #    self._to_visual_x,
        #    self._to_visual_y,
        #    layer=LAYER_SPRITES,
        # )
        self.graphics.refresh()
        return self._return_state(self._self_app_state)

    # ------------------------------------------------------------------
    # Layers
    # ------------------------------------------------------------------

    def _ensure_layers(self) -> None:
        """Create layers and clear maze-dependent content."""

        self.graphics.clear()
        self.graphics.fill(BLACK)
        self.graphics.set_layer_order(["main"])

        first_time = not self.graphics.has_layer(LAYER_MAZE)

        for name in LAYER_ORDER:
            if not self.graphics.has_layer(name):
                self.graphics.create_layer(name)

        if first_time:
            self.graphics.set_layer_order(LAYER_ORDER)
        else:
            self.graphics.clear(LAYER_MAZE)
            self.graphics.clear(LAYER_PACGUMS)
            self.graphics.clear(LAYER_VALUES)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render_cells(self) -> None:
        """Render maze cells using cached absolute geometry."""

        for index, name in enumerate(self._cell_names):
            cell = self._cell_cache.get(name)

            if cell is None:
                continue

            # color = WHITE if index % 2 == 0 else YELLOW

            # print(f"cell{index}:({cell.width},{cell.height})")

            self.graphics.draw_rectangle(
                x=cell.x,
                y=cell.y,
                width=cell.width,
                height=cell.height,
                color=BLACK,
                layer=LAYER_MAZE,
            )

    def _render_borders(self) -> None:
        """Render maze walls using cached absolute geometry."""

        for border_name in self._border_names:
            border = self._border_cache.get(border_name)

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

    def _render_top_bar(self) -> None:
        """Render the top-bar rectangles and labels."""

        for top_bar_name in self._top_bar_names:
            top_bar_rect = self._top_bar_cache.get(top_bar_name)

            if top_bar_rect is None:
                continue

            # Yellow background.
            # self.graphics.draw_rectangle(
            #    x=top_bar_rect.x,
            #    y=top_bar_rect.y,
            #    width=top_bar_rect.width,
            #    height=top_bar_rect.height,
            #    color=YELLOW,
            #    layer=LAYER_MAZE,
            # )

            # White label.
            if top_bar_rect.text is not None:
                self.graphics.draw_text(
                    text=top_bar_rect.text.text,
                    x=top_bar_rect.text.x,
                    y=top_bar_rect.text.y,
                    color=WHITE,
                    spacing=top_bar_rect.text.spacing,
                    scale=top_bar_rect.text.scale,
                    layer=LAYER_MAZE,
                )

    def _render_values(self) -> None:
        """Render the value rectangles and their text."""

        for value_name in self._value_names:
            value_rect = self._value_cache.get(value_name)

            if value_rect is None:
                continue

            # Black background.
            # self.graphics.draw_rectangle(
            #    x=value_rect.x,
            #    y=value_rect.y,
            #    width=value_rect.width,
            #    height=value_rect.height,
            #    color=BLACK,
            #    layer=LAYER_VALUES,
            # )

            # print(value_rect.text.text)
            # White value text.
            if value_rect.text is not None:
                self.graphics.draw_text(
                    text=value_rect.text.text,
                    x=value_rect.text.x,
                    y=value_rect.text.y,
                    color=WHITE,
                    spacing=value_rect.text.spacing,
                    scale=value_rect.text.scale,
                    layer=LAYER_VALUES,
                )

    def _render_pacgums(self) -> None:
        """Render all remaining pac-gums."""

        for pacgum_name in self._pacgum_names:
            pacgum = self._pacgum_cache[pacgum_name]

            self.graphics.draw_circle(
                pacgum.x,
                pacgum.y,
                pacgum.radius,
                PACGUM_COLOR,
                layer=LAYER_PACGUMS,
            )

        for super_pacgum_name in self._super_pacgum_names:
            super_pacgum = self._super_pacgum_cache[
                super_pacgum_name
            ]

            self.graphics.draw_circle(
                super_pacgum.x,
                super_pacgum.y,
                super_pacgum.radius,
                PACGUM_COLOR,
                layer=LAYER_PACGUMS,
            )

    def _render_pacman(self) -> None:
        self.graphics.draw_image(
            x=self._pac_man.x,
            y=self._pac_man.y,
            bits=list(self._pac_man.bit_map),
            line_len=self._pac_man.size,
            color=PACMAN_COLOR,
            layer=LAYER_SPRITES,
        )

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _rebuild_cache(self) -> None:
        """Rebuild pixel-based geometry and draw static layers."""

        self._cell_cache.clear()
        self._border_cache.clear()
        self._top_bar_cache.clear()
        self._value_cache.clear()
        self._pacgum_cache.clear()
        self._super_pacgum_cache.clear()

        self._cache_cells()
        self._cache_borders()
        self._cache_top_bar()
        self._cache_values()
        self._cache_pacgums()

        self._render_cells()
        self._render_borders()
        self._render_top_bar()
        self._render_values()
        self._render_pacgums()

    def _cache_cells(self) -> None:
        """Cache all maze cells in absolute pixel coordinates."""

        for cell_name in self._cell_names:
            rect = self.layout.get_rect_absolute(
                cell_name,
                self._width,
                self._height,
            )

            if rect is not None:
                self._cell_cache[cell_name] = rect

    def _cache_borders(self) -> None:
        """Cache all maze borders in absolute pixel coordinates."""

        for border_name in self._border_names:
            rect = self.layout.get_rect_absolute(
                border_name,
                self._width,
                self._height,
            )

            if rect is not None:
                self._border_cache[border_name] = rect

    def _cache_top_bar(self) -> None:
        """Cache top-bar rectangles in absolute pixel coordinates."""

        for top_bar_name in self._top_bar_names:
            if self._top_bar_scale == 0:
                rect = self.layout.get_rect_absolute(
                    top_bar_name,
                    self._width,
                    self._height,
                )

                if rect is None or rect.text is None:
                    continue

                self._top_bar_scale = rect.text.scale

            else:
                rect = self.layout.get_rect_absolute(
                    top_bar_name,
                    self._width,
                    self._height,
                    self._top_bar_scale,
                )

            if rect is None:
                continue

            rect.color = YELLOW

            if rect.text is not None:
                rect.text.color = WHITE

            self._top_bar_cache[top_bar_name] = rect

    def _cache_values(self) -> None:
        """Cache top-bar value rectangles in absolute coordinates."""

        for value_name in self._value_names:
            if self._value_scale == 0:
                rect = self.layout.get_rect_absolute(
                    value_name,
                    self._width,
                    self._height,
                )

                if rect is None or rect.text is None:
                    continue

                self._value_scale = rect.text.scale

            else:
                rect = self.layout.get_rect_absolute(
                    value_name,
                    self._width,
                    self._height,
                    self._value_scale,
                )

            if rect is None:
                continue

            rect.color = BLACK

            if rect.text is not None:
                rect.text.color = WHITE
                # print("cached text:", rect.text.text)
            self._value_cache[value_name] = rect

    def _cache_pacgums(self) -> None:
        """Cache the pixel position and radius of all pac-gums."""

        for pacgum_name in self._pacgum_names:
            abs_circle = self.layout.get_circle_absolute(
                pacgum_name,
                self._width,
                self._height,
            )

            if abs_circle is None:
                continue

            abs_circle.color = PACGUM_COLOR
            self._pacgum_cache[pacgum_name] = abs_circle

        for super_pacgum_name in self._super_pacgum_names:
            abs_circle = self.layout.get_circle_absolute(
                super_pacgum_name,
                self._width,
                self._height,
            )

            if abs_circle is None:
                print(f"NIGGER for {super_pacgum_name}")
                continue

            abs_circle.color = PACGUM_COLOR
            self._super_pacgum_cache[
                super_pacgum_name
            ] = abs_circle

    # ------------------------------------------------------------------
    # Maze
    # ------------------------------------------------------------------

    def _make_maze(self) -> None:
        """Generate the maze and create its percentage-based layout."""

        lvl = self.config.levels[self._level]
        print(lvl)

        self._maze_gen.generate()

        total_width = 100 - self.MARGIN_X * 2
        total_height = 100 - self.MARGIN_Y * 2

        maze_width = total_width
        maze_height = total_height - self.TOPBAR_HEIGHT

        # Available size of one cell in pixels.
        cell_width = (
            maze_width
            / lvl.width
            / 100
            * self._width
        )

        cell_height = (
            maze_height
            / lvl.height
            / 100
            * self._height
        )

        # Keep cells square.
        cell_size = min(cell_width, cell_height)
        self._cell_size_px = int(math.ceil(cell_size))

        cell_width_p = cell_size / self._width * 100
        cell_height_p = cell_size / self._height * 100

        final_maze_width = cell_width_p * lvl.width
        final_maze_height = cell_height_p * lvl.height

        final_total_width = final_maze_width
        final_total_height = (
            final_maze_height
            + self.TOPBAR_HEIGHT
        )

        margin_left = (100 - final_total_width) / 2
        margin_top = (100 - final_total_height) / 2

        # print("margin 0", self.MARGIN_X)

        self.MARGIN_X = margin_left
        self.MARGIN_Y = margin_top

        # print("margin 1", self.MARGIN_X)

        maze_top = margin_top + self.TOPBAR_HEIGHT

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

        border_x_thickness = (
            cell.widthp * self.BORDER_SIZE
        )

        border_y_thickness = (
            cell.heightp * self.BORDER_SIZE
        )

        if west:
            border_name = (
                f"{BORDER_PREFIX}{name}_WEST"
            )

            self.layout.add_rect(
                xp=cell.xp - border_x_thickness / 2,
                yp=cell.yp - border_y_thickness / 2,
                widthp=border_x_thickness,
                heightp=cell.heightp + border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if south:
            border_name = (
                f"{BORDER_PREFIX}{name}_SOUTH"
            )

            self.layout.add_rect(
                xp=cell.xp - border_x_thickness / 2,
                yp=cell.yp + cell.heightp
                - border_y_thickness / 2,
                widthp=cell.widthp + border_x_thickness,
                heightp=border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if east:
            border_name = (
                f"{BORDER_PREFIX}{name}_EAST"
            )

            self.layout.add_rect(
                xp=cell.xp + cell.widthp
                - border_x_thickness / 2,
                yp=cell.yp - border_y_thickness / 2,
                widthp=border_x_thickness,
                heightp=cell.heightp + border_y_thickness,
                name=border_name,
            )

            self._border_names.append(border_name)

        if north:
            border_name = (
                f"{BORDER_PREFIX}{name}_NORTH"
            )

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

        lvl = self.config.levels[self._level]

        corners = {
            0,
            lvl.width - 1,
            (lvl.height - 1) * lvl.width,
            lvl.width * lvl.height - 1,
        }

        available = [
            x
            for i, x in enumerate(self._cell_names)
            if i not in corners
            and self._cell_names[i] not in self._42_pattern
        ]

        selected_cell_names = random.sample(
            available,
            self.config.pacgum,
        )

        for cell_name in selected_cell_names:
            cell = self.layout.get_rect(cell_name)

            if cell is None:
                return

            pacgum_name = (
                f"{PACGUM_PREFIX}{cell_name}"
            )

            self.layout.add_circle(
                cell.xp + cell.widthp / 2,
                cell.yp + cell.heightp / 2,
                cell.widthp * (1.0 - self.BORDER_SIZE * 2) / 4,
                pacgum_name,
            )

            self._pacgum_names.append(pacgum_name)
        for corner in corners:
            cell = self.layout.get_rect(
                self._cell_names[corner]
            )

            if cell is None:
                return

            super_pacgum_name = (
                f"{SUPER_PACGUM_PREFIX}{corner}"
            )
            self.layout.add_circle(
                cell.xp + cell.widthp / 2,
                cell.yp + cell.heightp / 2,
                cell.widthp * (1.0 - self.BORDER_SIZE * 2) / 2,
                super_pacgum_name,
            )

            self._super_pacgum_names.append(
                super_pacgum_name
            )

    def _eat_pacgum(self, x: int, y: int) -> None:
        self._to_visual_x = x
        self._to_visual_y = y

        i = 0
        # print(self._pacgum_cache.keys())
        for pacgum_name in self._pacgum_names:
            abs_circle = self._pacgum_cache[pacgum_name]

            if abs_circle.contains(x, y):
                print("EATEN")

                del self._pacgum_cache[pacgum_name]
                del self._pacgum_names[i]
                self._score += self.config.points_per_pacgum
                self._recache_value(f"{VALUE_PREFIX}SCORE", str(self._score))
                # self._value_cache[f"{VALUE_PREFIX}SCORE"].text.text = str(
                #    self._score)

                self.graphics.clear(LAYER_PACGUMS)
                self.graphics.clear(LAYER_VALUES)
                self._render_pacgums()
                self._render_values()
                if not self._pacgum_names:
                    # self.STARTED = False
                    self._self_app_state = AppState.LEVEL_COMPLETE
                return
            i += 1
        # if i == 0:
        #    print("NEW LEVEL")
        #    self._level = 1
        #    self._return_state(AppState.GAME)
        #    self._start_screen()
        #    return
        i = 0
        for super_pacgum_name in self._super_pacgum_names:
            abs_circle = self._super_pacgum_cache[
                super_pacgum_name
            ]

            if abs_circle.contains(x, y):
                print("SUPER EATEN")

                del self._super_pacgum_cache[super_pacgum_name]
                del self._super_pacgum_names[i]
                self._score += self.config.points_per_super_pacgum

                self.graphics.clear(LAYER_PACGUMS)
                self.graphics.clear(LAYER_VALUES)
                self._render_pacgums()
                self._render_values()

                return
            i += 1

    # ------------------------------------------------------------------
    # Pac-Man
    # ------------------------------------------------------------------

    def _can_move(self, direction: Directions) -> bool:
        """Whether Pac-Man can leave its current logical cell."""

        if direction == Directions.STOP:
            return False

        walls = self._cell_walls.get(
            (self._pacman_col, self._pacman_row)
        )

        if walls is None:
            return False

        wall_key = DIRECTION_TO_WALL_KEY[direction]

        return not walls[wall_key]

    def _spawn_pacman(self, col: int, row: int) -> None:
        """Place Pac-Man at rest, centered on the given maze cell."""

        cell = self._cell_cache.get(
            f"{CELL_PREFIX}{col}_{row}"
        )

        if cell is None:
            return

        sprite_size = int(
            math.ceil(
                self._cell_size_px
                * (0.9 - self.BORDER_SIZE)
            )
        )

        center_x = (
            cell.x
            + cell.width // 2
            - sprite_size // 2
        )

        center_y = (
            cell.y
            + cell.height // 2
            - sprite_size // 2
        )

        self._pac_man = PacMan(
            x=center_x,
            y=center_y,
            cell_size=self._cell_size_px,
            size=sprite_size,
            speed=PACMAN_SPEED,
        )

        self._pacman_col = col
        self._pacman_row = row

    # ------------------------------------------------------------------
    # Top Bar
    # ------------------------------------------------------------------

    def _make_top_bar(self) -> None:
        """Create four equally sized top-bar information boxes."""

        top_bar_width = 100.0
        gap = 1.0

        # Four equal boxes and three equal gaps.
        box_width = (top_bar_width - gap * 3) / 4

        labels = [
            ("SCORE", "SCORE"),
            ("LIVES", "LIVES"),
            ("LEVEL", "LEVEL"),
            ("TIME", "TIME"),
        ]

        current_x = 0.0

        for name, text in labels:
            top_bar_name = f"{TOP_BAR_PREFIX}{name}"

            self.layout.add_rect(
                xp=current_x,
                # yp=self.MARGIN_Y - self.BORDER_SIZE * 2,
                yp=self.BORDER_SIZE,
                widthp=box_width,
                heightp=self.TOPBAR_HEIGHT,
                name=top_bar_name,
                text=text,
                y_offsetp_rev=50.0,
            )

            self._top_bar_names.append(top_bar_name)

            current_x += box_width + gap

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------

    def _make_values(self) -> None:
        """Create value rectangles below the top-bar labels."""

        top_bar_width = 100.0
        gap = 1.0

        # Four equal boxes and three equal gaps.
        box_width = (top_bar_width - gap * 3) / 4

        values = [
            ("SCORE", str(self._score)),
            ("LIVES", str(self._lives)),
            ("LEVEL", str(self._level)),
            ("TIME", str(self._time)),
        ]

        current_x = 0.0

        for name, text in values:
            value_name = f"{VALUE_PREFIX}{name}"

            self.layout.add_rect(
                xp=current_x,
                # yp=self.MARGIN_Y * 1.5 - self.BORDER_SIZE * 2,
                yp=self.BORDER_SIZE + self.TOPBAR_HEIGHT / 2,
                widthp=box_width,
                heightp=self.TOPBAR_HEIGHT / 2,
                name=value_name,
                text=text,
                y_offsetp=50.0,
            )

            self._value_names.append(value_name)

            current_x += box_width + gap

    def _recache_value(self, name: str, text: str) -> None:
        self.layout.change_text_rect(name, text)
        rect = self.layout.get_rect_absolute(
            name,
            self._width,
            self._height,
            self._value_scale
        )
        if rect is None or rect.text is None:
            return
        rect.color = BLACK
        rect.text.color = WHITE
        self._value_cache[name] = rect
