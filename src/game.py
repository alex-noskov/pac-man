from typing import Callable
from .models import Directions


class PacMan:
    """Track Pac-Man's pixel position and buffered grid-based movement."""

    def __init__(self, x: int, y: int,
                 cell_size: int, size: int,
                 speed: int,
                 def_dir: Directions = Directions.STOP) -> None:
        """Set pixel geometry, grid spacing, speed, and initial direction."""
        self.size = size
        self.bit_map = self._generate_circle_bitmap(size)
        self.x = x
        self.y = y

        # Distance in pixels between two adjacent cell centers, and how
        # many pixels pacman advances per frame while moving between them.
        self.cell_size = cell_size
        self.speed = speed

        self.direction = def_dir
        self.desired_direction = def_dir

        # The pixel position pacman is currently walking toward.
        # Equal to (x, y) whenever pacman is grid-aligned / at rest.
        self._target_x = x
        self._target_y = y

    def _generate_circle_bitmap(self, size: int) -> str:
        """Return a flattened binary circle bitmap of the given square size."""
        center = (size - 1) / 2
        radius = size / 2
        bitmap = []

        for r in range(size):
            row_str = ""
            for c in range(size):
                dist = ((r - center) ** 2 + (c - center) ** 2) ** 0.5
                if dist <= radius:
                    row_str += "1"
                else:
                    row_str += "0"
            bitmap.append(row_str)

        return "".join(bitmap)

    def set_direction(self, direction: Directions) -> None:
        """Buffer the requested direction for the next available grid turn."""
        self.desired_direction = direction

    def is_aligned(self) -> bool:
        """True when pacman sits exactly on a grid point (not mid-move)."""
        return self.x == self._target_x and self.y == self._target_y

    def warp_to(self, x: int, y: int) -> None:
        """Place pacman at an exact grid point, at rest (used on spawn)."""
        self.x = x
        self.y = y
        self._target_x = x
        self._target_y = y

    def move(self, can_move: Callable[[Directions], bool],
             eat_callback: Callable) -> Directions | None:
        """Advance one frame of grid-based movement.

        `can_move(direction)` must return True if there is no wall
        blocking movement out of pacman's *current* cell in that
        direction. It is only ever queried while pacman is aligned to
        the grid - turns and stops are decided only at cell centers,
        never mid-cell.

        Returns the direction pacman just committed to leaving its
        current cell in, if it started a new grid step this frame,
        otherwise None. The caller uses this to know when to update
        pacman's logical (col, row) position.
        """
        departed = None

        if self.is_aligned():
            eat_callback(self.x + self.size // 2,
                         self.y + self.size // 2)
            # Prefer the direction the player asked for; fall back to
            # continuing straight if the turn isn't available yet. The
            # desired direction is never cleared here - if it's still
            # blocked, it stays pending and gets re-checked at the next
            # cell center.
            if self.desired_direction != self.direction and \
                    can_move(self.desired_direction):
                self.direction = self.desired_direction

            if not can_move(self.direction):
                # Wall in every direction we're willing to take: stay put.
                return None

            dx, dy = self.direction.value
            self._target_x = self.x + dx * self.cell_size
            self._target_y = self.y + dy * self.cell_size
            departed = self.direction

        self._step_towards_target()
        return departed

    def _step_towards_target(self) -> None:
        """Advance pixel coordinates toward their targets without overshoot."""
        self.x += self._clamp_step(self._target_x - self.x)
        self.y += self._clamp_step(self._target_y - self.y)

    def _clamp_step(self, distance: int) -> int:
        """Return a signed step bounded by speed and remaining distance."""
        if distance == 0:
            return 0
        step = self.speed if distance > 0 else -self.speed
        return step if abs(step) < abs(distance) else distance
