"""Simple, slower ghost movement without shortest-path personalities."""
import unittest

from src.maze import Maze
from src.models import Directions
from src.parsing import Config, parse
from src.session import GameSession, Ghost


class SimpleGhostTests(unittest.TestCase):
    """Local choices satisfy chase/flee without a whole-maze AI search."""

    def test_shipped_and_default_ghost_speed_is_two_cells_per_second(
            self) -> None:
        """One obvious config key sets a visibly slower common ghost speed."""
        for config in (Config(), parse('config.json')):
            self.assertEqual(config.ghost_speed, 2.0)

    def test_chase_chooses_local_distance_not_a_shortest_path(self) -> None:
        """At an intersection choose the nearest neighboring cell locally."""
        game = GameSession(Config())
        game.maze = Maze(3, 3, [[9, 5, 3], [10, 15, 10], [14, 15, 14]])
        game.player.x, game.player.y = 2.0, 2.0
        ghost = Ghost(0.0, 1.0, spawn=(0, 1))
        game._choose_ghost_direction(ghost)
        # Down is locally closer, although the full route starts upward.
        self.assertEqual(ghost.desired_direction, Directions.DOWN)

    def test_intersection_does_not_immediately_reverse(self) -> None:
        """Avoid two-cell bouncing when another legal exit is available."""
        game = GameSession(Config())
        game.maze = Maze(3, 3, [[9, 1, 3], [8, 0, 2], [12, 4, 6]])
        game.player.x, game.player.y = 0.0, 1.0
        ghost = Ghost(1.0, 1.0, direction=Directions.RIGHT)
        game._choose_ghost_direction(ghost)
        self.assertNotEqual(ghost.desired_direction, Directions.LEFT)
        self.assertTrue(
            game.maze.can_move(ghost.cell, ghost.desired_direction))

    def test_dead_end_allows_reversing(self) -> None:
        """The anti-bounce rule must never trap a ghost in a dead end."""
        game = GameSession(Config())
        game.maze = Maze(3, 1, [[13, 5, 7]])
        game.player.x, game.player.y = 0.0, 0.0
        ghost = Ghost(2.0, 0.0, direction=Directions.RIGHT)
        game._choose_ghost_direction(ghost)
        self.assertEqual(ghost.desired_direction, Directions.LEFT)

    def test_edible_ghost_prefers_greater_local_distance(self) -> None:
        """The same distance calculation switches from chasing to fleeing."""
        game = GameSession(Config())
        game.maze = Maze(3, 3, [[9, 1, 3], [8, 0, 2], [12, 4, 6]])
        game.player.x, game.player.y = 2.0, 1.0
        ghost = Ghost(1.0, 1.0)
        game._choose_ghost_direction(ghost)
        self.assertEqual(ghost.desired_direction, Directions.RIGHT)
        game.power_remaining = 8.0
        game._choose_ghost_direction(ghost)
        self.assertNotEqual(ghost.desired_direction, Directions.RIGHT)

    def test_ghost_stops_when_there_are_no_corridors(self) -> None:
        """Malformed/disconnected test cells cannot make ghosts walk walls."""
        game = GameSession(Config())
        game.maze = Maze(1, 1, [[15]])
        ghost = Ghost(0.0, 0.0)
        game._choose_ghost_direction(ghost)
        self.assertEqual(ghost.desired_direction, Directions.STOP)
