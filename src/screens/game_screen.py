from .screen import Screen
from ..models import AppState
from ..graphics import Graphics
from ..parsing import Config
from mazegenerator import MazeGenerator
from ..colors import WHITE, BLACK, YELLOW
from ..events import Event, EventType
from ..ui import Layout, AbsoluteRect

TWO_BASE_TABLE = {
    0:  [0, 0, 0, 0],
    1:  [0, 0, 0, 1],
    2:  [0, 0, 1, 0],
    3:  [0, 0, 1, 1],
    4:  [0, 1, 0, 0],
    5:  [0, 1, 0, 1],
    6:  [0, 1, 1, 0],
    7:  [0, 1, 1, 1],
    8:  [1, 0, 0, 0],
    9:  [1, 0, 0, 1],
    10: [1, 0, 1, 0],
    11: [1, 0, 1, 1],
    12: [1, 1, 0, 0],
    13: [1, 1, 0, 1],
    14: [1, 1, 1, 0],
    15: [1, 1, 1, 1],
}


class GameScreen(Screen):
    """Gameplay screen"""

    def __init__(self, graphics: Graphics, config: Config) -> None:
        self.graphics = graphics
        self.layout = Layout()
        self._maze_gen = MazeGenerator()
        self._curr_cell_names: list = []
        self._cache: dict = {}
        self.config = config
        self._self_app_state = AppState.GAME

        sizes = self.graphics.get_window_size()
        self._width = sizes[0]
        self._height = sizes[1]

        self._make_maze(0)
        # self._cache: dict[str, AbsoluteRect] = {}

        # self._gen_layout()
        # self._cache_abs_layout()

    def handle_event(self, event: Event) -> AppState:
        """Handle an input event."""
        print(event.type)
        if event.type == EventType.CLOSE:
            return AppState.EXIT
        if event.type == EventType.KEY_ESC:
            return AppState.EXIT
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Render frame logic."""
        self.graphics.clear()

        # fact_width = fact_height = min(self._width, self._height)
        # fact_x_offset = (self._width - fact_width) // 2
        # fact_y_offset = (self._height - fact_height) // 2

        i = 0
        for cell_name in self._curr_cell_names:
            cell_abs_rect = self.layout.get_rect_absolute(
                cell_name, self._width, self._height)
            if i % 2 == 0:
                cell_abs_rect.color = WHITE
            else:
                cell_abs_rect.color = YELLOW
            self.graphics.draw_rectangle(
                x=cell_abs_rect.x,
                y=cell_abs_rect.y,
                width=cell_abs_rect.width,
                height=cell_abs_rect.height,
                color=cell_abs_rect.color
            )
            i += 1
        self.graphics.refresh()
        return self._self_app_state

    def _make_maze(self, cur_lvl: int) -> None:
        lvl = self.config.levels[cur_lvl]
        self._maze_gen.generate()

        margin_x = margin_y = 2
        print(margin_x, margin_y)
        total_height = 100 - margin_y * 2
        total_width = 100 - margin_x * 2
        print(total_height, total_width)
        topbar_height = 10
        maze_height = total_height - topbar_height
        maze_width = total_width
        print(maze_height, maze_width)
        cell_height = int(maze_height / lvl.height / 100 * self._height)
        cell_width = int(maze_width / lvl.width / 100 * self._width)
        print(cell_height, cell_width)
        cell_size = min(cell_height, cell_width)
        print(cell_size)
        cell_height_p = cell_size / self._height * 100
        cell_width_p = cell_size / self._width * 100
        print(cell_height_p, cell_width_p)
        final_maze_height = cell_height_p * lvl.height
        final_maze_width = cell_width_p * lvl.width
        print(final_maze_height, final_maze_width)
        final_total_height = final_maze_height + topbar_height
        final_total_width = final_maze_width
        print(final_total_height, final_total_width)
        final_margin_y = (100 - final_total_height) / 2
        final_margin_x = (100 - final_total_width) / 2
        print(final_margin_y, final_margin_x)
        final_margin_maze_y = final_margin_y + topbar_height
        print(final_margin_maze_y)
        # print(self._maze_gen.maze)
        # x_start = 5
        # y_start = 8
        # x_size = 90 // lvl.width
        # y_size = 90 // lvl.height
        xi = yi = 0
        for line in self._maze_gen.maze:
            xi = 0
            y_cur = final_margin_maze_y + cell_height_p * yi
            for cell in line:
                x_cur = final_margin_x + cell_width_p * xi
                self.layout.add_rect(xp=x_cur, yp=y_cur,
                                     widthp=cell_width_p,
                                     heightp=cell_height_p,
                                     name=f"CELL_{xi}_{yi}")
                # print(TWO_BASE_TABLE.get(cell))
                self._curr_cell_names.append(f"CELL_{xi}_{yi}")
                xi += 1
            yi += 1
