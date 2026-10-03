"""Headless adapter tests, including the assigned external generator."""
import unittest

from src.maze import Maze, MazeError
from src.models import Directions


class MazeTests(unittest.TestCase):
    def test_reciprocal_corridor_and_boundary(self) -> None:
        maze = Maze(2, 1, [[13, 7]])
        self.assertTrue(maze.can_move((0, 0), Directions.RIGHT))
        self.assertTrue(maze.can_move((1, 0), Directions.LEFT))
        self.assertFalse(maze.can_move((0, 0), Directions.UP))
        self.assertFalse(maze.can_move((0, 0), Directions.LEFT))
        self.assertFalse(maze.can_move((0, 0), Directions.STOP))
        self.assertEqual(maze.neighbors((0, 0)), [(1, 0)])
        self.assertEqual(maze.reachable((0, 0)), {(0, 0), (1, 0)})
        self.assertEqual(maze.distances((0, 0)), {(0, 0): 0, (1, 0): 1})

    def test_real_generator_is_deterministic_and_preserves_rng(self) -> None:
        import random
        state = random.getstate()
        first = Maze.generate(15, 15, 42)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first.cells, Maze.generate(15, 15, 42).cells)
        self.assertEqual((first.width, first.height), (15, 15))
        spawn = first.center_spawn
        self.assertNotEqual(first.cells[spawn[1]][spawn[0]], 15)
        reachable = first.reachable(spawn)
        self.assertTrue(set(first.corner_spawns) <= reachable)
        self.assertEqual(len(set(first.corner_spawns)), 4)
        self.assertTrue(all(first.neighbors(c) for c in reachable))

    def test_generator_errors_are_clean_and_restore_rng(self) -> None:
        import random
        from unittest.mock import patch
        state = random.getstate()
        with patch('mazegenerator.MazeGenerator',
                   side_effect=RuntimeError('bad')):
            with self.assertRaisesRegex(MazeError, 'bad'):
                Maze.generate(15, 15, 42)
        self.assertEqual(random.getstate(), state)

    def test_no_accessible_spawn_rejected(self) -> None:
        with self.assertRaises(MazeError):
            _ = Maze(1, 1, [[15]]).center_spawn

    def test_invalid_masks_dimensions_and_walls_rejected(self) -> None:
        invalid: list[tuple[int, int, list[list[int]]]] = [
            (0, 1, []), (2, 1, [[15]]), (1, 1, [[16]]),
            (1, 1, [[True]]), (1, 1, [[0]]), (2, 1, [[13, 15]]),
        ]
        for width, height, cells in invalid:
            with self.subTest(cells=cells), self.assertRaises(MazeError):
                Maze(width, height, cells)


if __name__ == '__main__':
    unittest.main()
