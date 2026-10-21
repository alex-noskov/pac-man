"""Pure gameplay model; no display, event loop or rendering dependencies."""
from dataclasses import dataclass
import math
import random
import secrets

from src.maze import Cell, Maze, MazeError
from src.models import AppState, Directions
from src.parsing import Config


@dataclass
class Actor:
    """Continuous grid-center position and queued corridor direction."""

    x: float
    y: float
    direction: Directions = Directions.STOP
    desired_direction: Directions = Directions.STOP

    @property
    def cell(self) -> Cell:
        """Return the last reached cell, not a prematurely rounded target."""
        dx, dy = self.direction.value
        x = math.ceil(self.x) if dx < 0 else math.floor(self.x)
        y = math.ceil(self.y) if dy < 0 else math.floor(self.y)
        return x, y


@dataclass
class Ghost(Actor):
    """An autonomous actor with its original corner and respawn timer."""

    spawn: Cell = (0, 0)
    respawn_remaining: float = 0.0


class GameSession:
    """Own a complete headless game with explicit application states."""

    def __init__(
        self,
        config: Config,
    ) -> None:
        """Start a new game using validated configuration."""
        self.config = config
        self.maze: Maze | None = None
        self.player = Actor(0.0, 0.0)
        self.ghosts: list[Ghost] = []
        self.pellets: set[Cell] = set()
        self.power_pellets: set[Cell] = set()
        self.error = ''
        self.state = AppState.GAME
        self.new_game()

    def new_game(self) -> None:
        """Reset score, lives and cheats; regenerate the fixed first level."""
        self.score = 0
        self.lives = self.config.lives
        self.level_index = 0
        self.time_remaining = 0.0
        self.power_remaining = 0.0
        self.cheat_enabled = False
        self.invincible = False
        self.ghosts_frozen = False
        self.speed_multiplier = 1.0
        self.grace_remaining = 0.0
        self.error = ''
        self._used_seeds: set[int] = set()
        self._load_level()

    def _load_level(self) -> None:
        """Generate one level or retain a clean error state on failure."""
        try:
            level = self.config.levels[self.level_index]
            if self.level_index == 0:
                seed = int(self.config.seed)
            else:
                seed = secrets.randbelow(2**31 - 1) + 1
                while seed in self._used_seeds:
                    seed = secrets.randbelow(2**31 - 1) + 1
            self._used_seeds.add(seed)
            self._random = random.Random(seed)
            maze = Maze.generate(
                level.width,
                level.height,
                seed,
            )
            center = maze.center_spawn
            corners = maze.corner_spawns
            self.maze = maze
            self.player = Actor(float(center[0]), float(center[1]))
            self.ghosts = [
                Ghost(
                    float(x),
                    float(y),
                    spawn=(x, y),
                )
                for x, y in corners
            ]
            self.power_pellets = set(corners) - {center}
            available = maze.reachable(center) - self.power_pellets - {center}
            amount = self.config.pacgum
            if amount == 0:
                self.pellets = available
            else:
                amount = min(
                    amount,
                    len(available),
                )
                selected = self._random.sample(
                    sorted(available),
                    amount,
                )
                self.pellets = set(selected)
            self.time_remaining = float(
                self.config.level_max_time
            )
            self.power_remaining = 0.0
            self.grace_remaining = 0.0
            self.error = ''
            self.state = AppState.GAME
        except (
            MazeError,
            ValueError,
            IndexError,
            TypeError,
        ) as exc:
            self.maze = None
            self.pellets.clear()
            self.power_pellets.clear()
            self.ghosts.clear()
            self.error = str(exc)
            self.state = AppState.ERROR

    def set_direction(
        self,
        direction: Directions,
    ) -> None:
        """Queue a turn, executed only when the next cell center permits it."""
        if self.state == AppState.GAME and isinstance(direction, Directions):
            self.player.desired_direction = direction

    def toggle_pause(self) -> None:
        """Pause/resume gameplay without touching any positions or timers."""
        if self.state == AppState.GAME:
            self.state = AppState.PAUSE
        elif self.state == AppState.PAUSE:
            self.state = AppState.GAME

    @staticmethod
    def _at_center(actor: Actor) -> bool:
        """Return whether an actor is exactly aligned to a grid center."""
        return (
            abs(actor.x - round(actor.x)) < 1e-9
            and
            abs(actor.y - round(actor.y)) < 1e-9
        )

    def _move(
        self,
        actor: Actor,
        distance: float,
    ) -> None:
        """Advance continuously; turns and wall checks happen at centers."""
        maze = self.maze
        if maze is None:
            return
        while distance > 1e-9:
            if self._at_center(actor):
                actor.x = float(round(actor.x))
                actor.y = float(round(actor.y))
                cell = actor.cell
                if isinstance(actor, Ghost):
                    self._choose_ghost_direction(actor)
                desired = actor.desired_direction
                if desired == Directions.STOP:
                    actor.direction = Directions.STOP
                elif maze.can_move(
                    cell,
                    desired
                ):
                    actor.direction = desired
                if not maze.can_move(
                    cell,
                    actor.direction
                ):
                    actor.direction = Directions.STOP
                    return
            dx, dy = actor.direction.value
            if dx == 0 and dy == 0:
                return
            if dx:
                target = (
                    math.floor(actor.x + 1e-9) + 1
                    if dx > 0
                    else math.ceil(actor.x - 1e-9) - 1
                )
                remaining = abs(target - actor.x)
            else:
                target = (
                    math.floor(actor.y + 1e-9) + 1
                    if dy > 0
                    else math.ceil(actor.y - 1e-9) - 1
                )
                remaining = abs(target - actor.y)
            step = min(distance, remaining)
            actor.x += dx * step
            actor.y += dy * step
            distance -= step
            if step >= remaining - 1e-9:
                actor.x, actor.y = (
                    float(round(actor.x)),
                    float(round(actor.y)),
                )
                if actor is self.player:
                    self._collect()
                    if self.state != AppState.GAME:
                        return

    def _choose_ghost_direction(
        self,
        ghost: Ghost,
    ) -> None:
        """Choose a nearby corridor toward or away from the player."""
        maze = self.maze
        if maze is None:
            return
        choices = maze.neighbors(ghost.cell)
        if not choices:
            ghost.desired_direction = Directions.STOP
            return
        fleeing = self.power_remaining > 0
        if not fleeing and len(choices) > 1:
            dx, dy = ghost.direction.value
            previous_cell = (
                ghost.cell[0] - dx,
                ghost.cell[1] - dy,
            )
            choices = [
                cell for cell in choices if cell != previous_cell
            ]

        best_distance: float | None = None
        best_choices: list[Cell] = []
        for x, y in choices:

            distance = (
                abs(x - self.player.x)
                + abs(y - self.player.y)
            )

            if (
                best_distance is None
                or (fleeing and distance > best_distance)
                or (not fleeing and distance < best_distance)
            ):
                best_distance = distance
                best_choices = [(x, y)]
            elif distance == best_distance:
                best_choices.append((x, y))

        if len(best_choices) == 1:
            target = best_choices[0]
        else:
            target = self._random.choice(best_choices)
        dx, dy = target[0] - ghost.cell[0], target[1] - ghost.cell[1]
        ghost.desired_direction = Directions((dx, dy))

    @staticmethod
    def _swept_touch(
        player_start: tuple[float, float],
        player: Actor,
        ghost_start: tuple[float, float],
        ghost: Ghost,
    ) -> bool:
        """Detect closest approach of simultaneous motion, including swaps."""
        relative_x = player_start[0] - ghost_start[0]
        relative_y = player_start[1] - ghost_start[1]
        relative_move_x = (
            (player.x - player_start[0])
            - (ghost.x - ghost_start[0])
        )
        relative_move_y = (
            (player.y - player_start[1])
            - (ghost.y - ghost_start[1])
        )
        relative_travel_squared = (
            relative_move_x * relative_move_x
            + relative_move_y * relative_move_y
        )
        if relative_travel_squared == 0:
            closest_time = 0.0
        else:
            closest_time = -(
                relative_x * relative_move_x
                + relative_y * relative_move_y
            )
            closest_time /= relative_travel_squared
            # Clamp to this step: 0 is its start and 1 is its end.
            closest_time = max(0.0, min(1.0, closest_time))
        # Actors touch when their closest separation is within 0.35 cells.
        return (
            (relative_x + closest_time * relative_move_x)**2
            + (relative_y + closest_time * relative_move_y)**2 <= 0.35**2
        )

    def _collisions(
        self,
        player_start: tuple[float, float],
        ghost_starts: list[tuple[float, float]],
    ) -> bool:
        """Resolve ghosts once; return True immediately after one death."""
        for ghost, start in zip(
            self.ghosts,
            ghost_starts
        ):
            if ghost.respawn_remaining > 0:
                continue
            if not self._swept_touch(player_start, self.player, start, ghost):
                continue
            if self.power_remaining > 0:
                self.score += self.config.points_per_ghost
                ghost.respawn_remaining = self.config.ghost_respawn_time
                ghost.x = float(ghost.spawn[0])
                ghost.y = float(ghost.spawn[1])
                ghost.direction = Directions.STOP
                ghost.desired_direction = Directions.STOP
            elif not self.invincible and self.grace_remaining <= 0:
                self.lives -= 1
                self.power_remaining = 0.0
                if self.lives <= 0:
                    self.state = AppState.GAME_OVER
                else:
                    self._reset_positions()
                return True
        return False

    def _reset_positions(self) -> None:
        """Restore center/corner positions and grant brief respawn immunity."""
        if self.maze is None:
            return
        spawn_x, spawn_y = self.maze.center_spawn
        self.player.x = float(spawn_x)
        self.player.y = float(spawn_y)
        self.player.direction = Directions.STOP
        self.player.desired_direction = Directions.STOP
        for ghost in self.ghosts:
            ghost.x = float(ghost.spawn[0])
            ghost.y = float(ghost.spawn[1])
            ghost.direction = Directions.STOP
            ghost.desired_direction = Directions.STOP
            ghost.respawn_remaining = 0.0
        self.grace_remaining = 1.5

    def _collect(self) -> None:
        """Collect dots only at reached cell centers and complete the level."""
        if not self._at_center(self.player):
            return
        cell = self.player.cell
        if cell in self.pellets:
            self.pellets.remove(cell)
            self.score += self.config.points_per_pacgum
        if cell in self.power_pellets:
            self.power_pellets.remove(cell)
            self.score += self.config.points_per_super_pacgum
            self.power_remaining = self.config.power_duration
        if not self.pellets:
            self.state = AppState.LEVEL_COMPLETE

    def update(
        self,
        dt: float,
    ) -> None:
        """Advance active gameplay using small continuous-time steps."""
        if (
            self.state != AppState.GAME
            or self.maze is None
            or not math.isfinite(dt)
            or dt <= 0
        ):
            return
        if self.time_remaining <= 0:
            self.time_remaining = 0.0
            self.state = AppState.GAME_OVER
            return
        remaining = min(dt, self.time_remaining)
        player_speed = self.config.player_speed
        player_speed *= self.speed_multiplier
        ghost_speed = self.config.ghost_speed
        while remaining > 1e-9 and self.state == AppState.GAME:
            step = min(
                remaining,
                1 / 60,
                0.1 / max(player_speed, ghost_speed, 1.0)
            )
            if self.power_remaining > 1e-9:
                step = min(step, self.power_remaining)
            # Collect first: a power pellet protects against existing contact.
            self._collect()
            if self.state != AppState.GAME:
                break
            player_start = self.player.x, self.player.y
            ghost_starts = [(g.x, g.y) for g in self.ghosts]
            if self._collisions(player_start, ghost_starts):
                break
            self._move(self.player, player_speed * step)
            for ghost in self.ghosts:
                if ghost.respawn_remaining > 0:
                    ghost.respawn_remaining = max(
                        0.0, ghost.respawn_remaining - step)
                    if ghost.respawn_remaining < 1e-9:
                        ghost.respawn_remaining = 0.0
                    continue
                if not self.ghosts_frozen:
                    self._move(ghost, ghost_speed * step)
            self._collect()
            died = self._collisions(player_start, ghost_starts)
            # Contact is resolved before edible/grace/level timers decrease.
            self.power_remaining = max(0.0, self.power_remaining - step)
            self.grace_remaining = max(0.0, self.grace_remaining - step)
            if self.power_remaining < 1e-9:
                self.power_remaining = 0.0
            self.time_remaining = max(0.0, self.time_remaining - step)
            if self.time_remaining < 1e-9:
                self.time_remaining = 0.0
                if self.state == AppState.GAME:
                    self.state = AppState.GAME_OVER
            remaining -= step
            if died:
                break

    def cheat(
        self,
        action: str,
    ) -> None:
        """Apply evaluator aids only during active gameplay and cheat mode."""
        if (
            not self.cheat_enabled
            or self.state not in (AppState.GAME, AppState.PAUSE)
        ):
            return
        if action == 'invincible':
            self.invincible = not self.invincible
        elif action == 'freeze':
            self.ghosts_frozen = not self.ghosts_frozen
        elif action == 'life':
            self.lives += 1
        elif action == 'speed':
            self.speed_multiplier = (
                2.0 if self.speed_multiplier == 1.0 else 1.0)
        elif action == 'power':
            self.power_remaining = self.config.power_duration
        elif action == 'skip':
            self.skip_level()

    def skip_level(self) -> None:
        """Complete the current level without manufacturing score."""
        if self.state in (AppState.GAME, AppState.PAUSE):
            self.pellets.clear()
            self.power_pellets.clear()
            self.state = AppState.LEVEL_COMPLETE

    def next_level(self) -> None:
        """Advance after completion, preserving score and remaining lives."""
        if self.state != AppState.LEVEL_COMPLETE:
            return
        if self.level_index + 1 >= len(self.config.levels):
            self.state = AppState.VICTORY
        else:
            self.level_index += 1
            self._load_level()
