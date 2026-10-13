"""Validated, graphics-independent adapter for the assigned maze package."""
from collections import deque
import random
from threading import RLock
from typing import Iterable

from src.models import Directions

Cell = tuple[int, int]
WALLS = {Directions.UP: (1, 4), Directions.RIGHT: (2, 8),
         Directions.DOWN: (4, 1), Directions.LEFT: (8, 2)}
_GENERATION_LOCK = RLock()


class MazeError(ValueError):
    """Report invalid maze data or an external generator failure."""


class Maze:
    """Own a validated row-major grid of N/E/S/W wall bitmasks."""

    def __init__(
        self,
        width: int,
        height: int,
        cells: Iterable[Iterable[int]],
    ) -> None:
        """Validate dimensions, boundaries and reciprocal wall masks."""
        if (type(width) is not int or type(height) is not int
                or width < 1 or height < 1):
            raise MazeError('Maze dimensions must be positive integers')
        self.width = width
        self.height = height
        try:
            self.cells = tuple(tuple(row) for row in cells)
        except TypeError as exc:
            raise MazeError('Maze cells must be a rectangular grid') from exc
        if (len(self.cells) != height
                or any(len(row) != width for row in self.cells)):
            raise MazeError('Maze grid does not match its dimensions')
        for y, row in enumerate(self.cells):
            for x, mask in enumerate(row):
                if type(mask) is not int or not 0 <= mask <= 15:
                    raise MazeError(
                        'Maze wall masks must be integers in 0..15')
        for y, row in enumerate(self.cells):
            for x, mask in enumerate(row):
                for direction, (wall, opposite) in WALLS.items():
                    dx, dy = direction.value
                    nx, ny = x + dx, y + dy
                    if not self.in_bounds((nx, ny)):
                        if not mask & wall:
                            raise MazeError('Maze has an open outer boundary')
                    elif bool(mask & wall) != bool(
                            self.cells[ny][nx] & opposite):
                        raise MazeError('Maze has non-reciprocal walls')

    @classmethod
    def generate(
        cls,
        width: int,
        height: int,
        seed: int,
    ) -> 'Maze':
        """Call the assigned generator as-is, restoring global RNG state."""
        with _GENERATION_LOCK:
            state = random.getstate()
            try:
                from mazegenerator import MazeGenerator
                if (type(width) is not int or type(height) is not int
                        or width < 2 or height < 2):
                    raise MazeError('Generated mazes must be at least 2 by 2')
                generated = MazeGenerator((width, height), perfect=False,
                                          seed=int(seed))
                return cls(width, height, generated.maze)
            except Exception as exc:
                raise MazeError(f'Maze generation failed: {exc}') from exc
            finally:
                random.setstate(state)

    @property
    def accessible_cells(self) -> set[Cell]:
        """Return cells with at least one passage (exclude solid 42 cells)."""
        return {(x, y) for y, row in enumerate(self.cells)
                for x, mask in enumerate(row) if mask != 15}

    @property
    def center_spawn(self) -> Cell:
        """Find the accessible cell nearest the geometric maze center."""
        cells = self.accessible_cells
        if not cells:
            raise MazeError('Maze has no accessible corridors')
        cx, cy = (self.width - 1) / 2, (self.height - 1) / 2
        return min(cells, key=lambda c: (
            abs(c[0] - cx) + abs(c[1] - cy), c[1], c[0]))

    @property
    def corner_spawns(self) -> tuple[Cell, ...]:
        """Find reachable cells nearest each corner, distinct if possible."""
        available = self.reachable(self.center_spawn)
        result: list[Cell] = []
        for cx, cy in ((0, 0), (self.width - 1, 0),
                       (self.width - 1, self.height - 1),
                       (0, self.height - 1)):
            choices = available - set(result) or available
            result.append(min(choices, key=lambda c: (
                abs(c[0] - cx) + abs(c[1] - cy), c[1], c[0])))
        return tuple(result)

    def in_bounds(
        self,
        cell: Cell,
    ) -> bool:
        """Return whether a cell is inside the grid."""
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def can_move(
        self,
        cell: Cell,
        direction: Directions,
    ) -> bool:
        """Check both sides of a corridor; STOP is never a passage."""
        if direction not in WALLS or not self.in_bounds(cell):
            return False
        x, y = cell
        dx, dy = direction.value
        target = x + dx, y + dy
        wall, opposite = WALLS[direction]
        return (self.in_bounds(target) and not self.cells[y][x] & wall
                and not self.cells[target[1]][target[0]] & opposite)

    def neighbors(
        self,
        cell: Cell,
    ) -> list[Cell]:
        """Return neighboring cells connected by legal corridors."""
        x, y = cell
        return [(x + d.value[0], y + d.value[1]) for d in WALLS
                if self.can_move(cell, d)]

    def distances(
        self,
        start: Cell,
    ) -> dict[Cell, int]:
        """Compute shortest graph distances with breadth-first search."""
        if not self.in_bounds(start):
            return {}
        distances = {start: 0}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for neighbor in self.neighbors(cell):
                if neighbor not in distances:
                    distances[neighbor] = distances[cell] + 1
                    queue.append(neighbor)
        return distances

    def reachable(
        self,
        start: Cell,
    ) -> set[Cell]:
        """Return the connected component containing start."""
        return set(self.distances(start))
