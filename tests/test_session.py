"""Gameplay contracts exercised without a display or graphics backend."""
import unittest
from unittest.mock import patch

from src.maze import Maze, MazeError
from src.models import AppState, Directions
from src.parsing import Config
from src.session import GameSession, Ghost


class SessionTests(unittest.TestCase):
    def arena(self) -> GameSession:
        """Use a tiny open room to exercise exact continuous motion."""
        game = GameSession(Config(pacgum=0))
        game.maze = Maze(3, 3, [[9, 1, 3], [8, 0, 2], [12, 4, 6]])
        game.player.x, game.player.y = 1.0, 1.0
        game.ghosts = []
        game.pellets = {(0, 0)}
        game.power_pellets = set()
        return game

    def test_crossed_centers_collect_even_with_fractional_frame(self) -> None:
        game = self.arena()
        game.maze = Maze(4, 1, [[13, 5, 5, 7]])
        game.player.x, game.player.y = 0.0, 0.0
        game.pellets = {(1, 0), (2, 0), (3, 0)}
        game.set_direction(Directions.RIGHT)
        game.update(0.03)
        game.update(0.4)
        self.assertEqual(game.pellets, {(3, 0)})
        self.assertEqual(game.score, 2 * game.config.points_per_pacgum)
        self.assertAlmostEqual(game.player.x, 2.15)

    def test_ghosts_chase_graph_distance_and_flee_when_powered(self) -> None:
        game = self.arena()
        game.player.x, game.player.y = 2.0, 1.0
        ghost = Ghost(1.0, 1.0, spawn=(0, 0))
        game.ghosts = [ghost]
        game.invincible = True
        game.update(0.1)
        self.assertAlmostEqual(ghost.x, 1.4)
        self.assertEqual(ghost.y, 1.0)
        ghost.x, ghost.y = 1.0, 1.0
        ghost.direction = Directions.STOP
        game.power_remaining = 2.0
        game.update(0.1)
        self.assertGreater(abs(ghost.x - 2.0) + abs(ghost.y - 1.0), 1.0)

    def test_ghost_uses_graph_not_manhattan_distance(self) -> None:
        game = self.arena()
        # A winding single corridor: moving down first is a trap/dead-end;
        # the shortest legal route to the player begins by moving up.
        game.maze = Maze(3, 3, [[9, 5, 3], [10, 15, 10], [14, 15, 14]])
        game.player.x, game.player.y = 2.0, 2.0
        game.pellets = {(1, 0)}
        ghost = Ghost(0.0, 1.0, spawn=(0, 1))
        game.ghosts = [ghost]
        game.update(0.1)
        self.assertAlmostEqual(ghost.y, 0.6)
        self.assertEqual(ghost.direction, Directions.UP)

    def test_touch_loses_only_one_life_and_resets_with_grace(self) -> None:
        game = self.arena()
        game.ghosts = [Ghost(1.0, 1.0, spawn=(0, 0)) for _ in range(4)]
        game.player.direction = Directions.RIGHT
        game.player.desired_direction = Directions.RIGHT
        game.power_remaining = 0.0
        game.update(2.0)
        self.assertEqual(game.lives, 2)
        assert game.maze is not None
        self.assertEqual(game.player.cell, game.maze.center_spawn)
        self.assertEqual(game.player.direction, Directions.STOP)
        self.assertEqual(game.player.desired_direction, Directions.STOP)
        self.assertGreater(game.grace_remaining, 0.0)
        for ghost in game.ghosts:
            self.assertEqual(ghost.cell, ghost.spawn)
            self.assertEqual(ghost.direction, Directions.STOP)
            ghost.x, ghost.y = game.player.x, game.player.y
        game.update(0.1)
        self.assertEqual(game.lives, 2)

    def test_last_life_ends_game_and_stops_updates(self) -> None:
        game = self.arena()
        game.lives = 1
        game.ghosts = [Ghost(1.0, 1.0)]
        game.update(0.01)
        self.assertEqual(game.state, AppState.GAME_OVER)
        self.assertEqual(game.lives, 0)
        score = game.score
        game.update(10.0)
        self.assertEqual(game.score, score)

    def test_midstep_collision_cannot_tunnel_or_swap(self) -> None:
        game = self.arena()
        game.player.x, game.player.y = 0.0, 1.0
        game.ghosts = [Ghost(2.0, 1.0, spawn=(2, 1))]
        game.set_direction(Directions.RIGHT)
        game.update(0.5)
        self.assertEqual(game.lives, 2)

    def test_edible_ghost_scores_once_and_respawns_after_five_seconds(
            self) -> None:
        game = self.arena()
        ghost = Ghost(1.0, 1.0, spawn=(2, 2))
        game.ghosts = [ghost]
        game.ghosts_frozen = True
        game.power_remaining = 8.0
        game.update(0.01)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.score, game.config.points_per_ghost)
        self.assertGreater(ghost.respawn_remaining, 4.9)
        game.toggle_pause()
        respawn = ghost.respawn_remaining
        game.update(3.0)
        self.assertEqual(ghost.respawn_remaining, respawn)
        game.toggle_pause()
        game.update(4.8)
        self.assertGreater(ghost.respawn_remaining, 0.0)
        self.assertEqual(game.score, game.config.points_per_ghost)
        game.update(0.3)
        self.assertEqual(ghost.respawn_remaining, 0.0)
        self.assertEqual((ghost.x, ghost.y), (2.0, 2.0))

    def test_cheats_are_gated_and_actions_work(self) -> None:
        game = self.arena()
        lives = game.lives
        actions = ('invincible', 'freeze', 'life', 'speed', 'power', 'skip')
        for action in actions:
            game.cheat(action)
        self.assertFalse(game.invincible)
        self.assertFalse(game.ghosts_frozen)
        self.assertEqual(game.lives, lives)
        self.assertEqual(game.power_remaining, 0.0)
        self.assertEqual(game.state, AppState.GAME)
        game.cheat_enabled = True
        game.cheat('invincible')
        game.cheat('freeze')
        game.cheat('life')
        game.cheat('speed')
        game.cheat('power')
        self.assertTrue(game.invincible)
        self.assertTrue(game.ghosts_frozen)
        self.assertEqual(game.lives, lives + 1)
        self.assertEqual(game.power_remaining, 8.0)
        game.set_direction(Directions.RIGHT)
        game.update(0.05)
        self.assertAlmostEqual(game.player.x, 1.5)
        game.cheat('unknown')
        game.cheat('skip')
        self.assertEqual(game.state, AppState.LEVEL_COMPLETE)

    def test_invincibility_freeze_and_power_expiration(self) -> None:
        game = self.arena()
        game.ghosts = [Ghost(1.0, 1.0, spawn=(0, 0))]
        game.cheat_enabled = True
        game.cheat('invincible')
        game.cheat('freeze')
        game.update(0.1)
        self.assertEqual(game.lives, 3)
        self.assertEqual((game.ghosts[0].x, game.ghosts[0].y), (1.0, 1.0))
        game.cheat('invincible')
        game.power_remaining = 0.01
        game.ghosts[0].x, game.ghosts[0].y = 0.0, 0.0
        game.update(0.02)
        self.assertEqual(game.power_remaining, 0.0)
        game.ghosts[0].x, game.ghosts[0].y = 1.0, 1.0
        game.update(0.01)
        self.assertEqual(game.lives, 2)

    def test_existing_power_applies_to_contact_at_frame_start(self) -> None:
        game = self.arena()
        game.ghosts = [Ghost(1.0, 1.0)]
        game.power_remaining = 0.001
        game.update(0.01)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.score, game.config.points_per_ghost)

    def test_zero_timer_is_immediate_game_over(self) -> None:
        game = self.arena()
        game.time_remaining = 0.0
        game.update(0.1)
        self.assertEqual(game.state, AppState.GAME_OVER)

    def test_positive_pellet_count_clamped_to_reachable_cells(self) -> None:
        game = GameSession(Config(pacgum=99999))
        assert game.maze is not None
        reachable = game.maze.reachable(game.player.cell)
        self.assertEqual(game.pellets | game.power_pellets,
                         reachable - {game.player.cell})

    def test_walk_every_real_level_to_victory_without_skip(self) -> None:
        game = GameSession(Config(pacgum=0, player_speed=30,
                                  level_max_time=500))
        game.cheat_enabled = True
        game.cheat('invincible')
        game.cheat('freeze')
        for index in range(10):
            self.assertEqual(game.level_index, index)
            maze = game.maze
            assert maze is not None
            start = game.player.cell
            visited = {start}
            stack = [(start, iter(maze.neighbors(start)))]
            route = []
            while stack:
                cell, neighbors = stack[-1]
                neighbor = next(neighbors, None)
                if neighbor is None:
                    stack.pop()
                    if stack:
                        route.append(stack[-1][0])
                elif neighbor not in visited:
                    visited.add(neighbor)
                    route.append(neighbor)
                    stack.append((neighbor, iter(maze.neighbors(neighbor))))
            minimum_score = (game.score
                             + len(game.pellets)
                             * game.config.points_per_pacgum
                             + len(game.power_pellets)
                             * game.config.points_per_super_pacgum)
            for target in route:
                cell = game.player.cell
                game.set_direction(Directions((target[0] - cell[0],
                                               target[1] - cell[1])))
                game.update(1 / game.config.player_speed)
                if game.state == AppState.LEVEL_COMPLETE:
                    break
                self.assertEqual(game.state, AppState.GAME)
                self.assertEqual(game.player.cell, target)
            self.assertEqual(game.state, AppState.LEVEL_COMPLETE)
            self.assertFalse(game.pellets | game.power_pellets)
            self.assertGreaterEqual(game.score, minimum_score)
            self.assertEqual(game.lives, game.config.lives)
            game.next_level()
        self.assertEqual(game.state, AppState.VICTORY)

    def test_continuous_movement_queued_turn_and_wall_stop(self) -> None:
        game = self.arena()
        game.set_direction(Directions.RIGHT)
        game.update(0.12)
        self.assertAlmostEqual(game.player.x, 1.6)
        self.assertEqual(game.player.cell, (1, 1))
        game.set_direction(Directions.DOWN)
        game.update(0.08)
        self.assertAlmostEqual(game.player.x, 2.0)
        self.assertAlmostEqual(game.player.y, 1.0)
        self.assertEqual(game.player.cell, (2, 1))
        game.update(0.2)
        self.assertEqual((game.player.x, game.player.y), (2.0, 2.0))
        game.update(1.0)
        self.assertEqual((game.player.x, game.player.y), (2.0, 2.0))

    def test_left_movement_cell_does_not_round_before_arrival(self) -> None:
        game = self.arena()
        game.set_direction(Directions.LEFT)
        game.update(0.12)
        self.assertAlmostEqual(game.player.x, 0.4)
        self.assertEqual(game.player.cell, (1, 1))
        game.update(0.08)
        self.assertEqual(game.player.cell, (0, 1))

    def test_items_collected_only_at_centers_and_all_required(self) -> None:
        game = self.arena()
        game.pellets = {(2, 1)}
        game.power_pellets = {(2, 2)}
        game.set_direction(Directions.RIGHT)
        game.update(0.12)
        self.assertEqual(game.score, 0)
        self.assertIn((2, 1), game.pellets)
        game.update(0.08)
        self.assertEqual(game.score, game.config.points_per_pacgum)
        self.assertEqual(game.state, AppState.GAME)
        game.set_direction(Directions.DOWN)
        game.update(0.2)
        self.assertEqual(game.state, AppState.LEVEL_COMPLETE)
        self.assertEqual(game.score, game.config.points_per_pacgum
                         + game.config.points_per_super_pacgum)
        self.assertGreater(game.power_remaining, 0)

    def test_pause_freezes_every_timer_and_position(self) -> None:
        game = self.arena()
        game.set_direction(Directions.RIGHT)
        game.power_remaining = 3.0
        before = (game.time_remaining, game.player.x, game.power_remaining)
        game.toggle_pause()
        self.assertEqual(game.state, AppState.PAUSE)
        game.update(4.0)
        self.assertEqual((game.time_remaining, game.player.x,
                          game.power_remaining), before)
        game.toggle_pause()
        game.update(0.1)
        self.assertAlmostEqual(game.player.x, 1.5)
        self.assertAlmostEqual(game.power_remaining, 2.9)
        self.assertAlmostEqual(game.time_remaining, before[0] - 0.1)

    def test_timeout_and_invalid_delta(self) -> None:
        game = self.arena()
        time = game.time_remaining
        for dt in (-1.0, float('nan'), float('inf'), 0.0):
            game.update(dt)
        self.assertEqual(game.time_remaining, time)
        game.time_remaining = 0.1
        game.update(1.0)
        self.assertEqual(game.state, AppState.GAME_OVER)
        self.assertEqual(game.time_remaining, 0.0)

    def test_new_game_reachable_items_and_reset(self) -> None:
        config = Config(pacgum=0)
        game = GameSession(config)
        self.assertEqual(game.state, AppState.GAME)
        self.assertEqual(game.lives, config.lives)
        self.assertEqual(len(game.ghosts), 4)
        self.assertEqual(len(game.power_pellets), 4)
        assert game.maze is not None
        self.assertEqual(game.player.cell, game.maze.center_spawn)
        reachable = game.maze.reachable(game.player.cell)
        self.assertTrue(game.pellets | game.power_pellets <= reachable)
        self.assertEqual(game.pellets | game.power_pellets,
                         reachable - {game.player.cell})
        self.assertFalse(game.pellets & game.power_pellets)
        first = game.maze.cells
        game.score = 1000
        game.lives = 1
        game.cheat_enabled = True
        game.new_game()
        self.assertEqual((game.score, game.lives, game.level_index),
                         (0, config.lives, 0))
        self.assertFalse(game.cheat_enabled)
        assert game.maze is not None
        self.assertEqual(game.maze.cells, first)

    def test_generator_failure_becomes_error_state(self) -> None:
        with patch.object(Maze, 'generate', side_effect=MazeError('broken')):
            game = GameSession(Config())
        self.assertEqual(game.state, AppState.ERROR)
        self.assertIn('broken', game.error)

    def test_levels_keep_score_lives_and_use_fresh_seeds(self) -> None:
        config = Config()
        game = GameSession(config)
        game.score = 123
        game.lives = 2
        original = Maze.generate
        with patch.object(Maze, 'generate', wraps=original) as generate:
            for index in range(len(config.levels)):
                self.assertEqual(game.level_index, index)
                game.skip_level()
                self.assertEqual(game.state, AppState.LEVEL_COMPLETE)
                game.next_level()
            self.assertEqual(game.state, AppState.VICTORY)
            seeds = [call.args[2] for call in generate.call_args_list]
        self.assertEqual(len(set(seeds)), len(config.levels) - 1)
        self.assertNotIn(int(config.seed), seeds)
        self.assertEqual((game.score, game.lives), (123, 2))


if __name__ == '__main__':
    unittest.main()
