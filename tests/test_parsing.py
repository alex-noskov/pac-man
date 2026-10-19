"""Regression tests for safe configuration defaults."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from src.parsing import Config, parse


class ParsingTests(unittest.TestCase):
    """Exercise config files through the public parser."""

    def test_seed_must_be_a_positive_integer_for_reproducible_first_level(
            self) -> None:
        """Vendor seed zero is random, so invalid seeds must use defaults."""
        for value in ('0', '-1', 'oops', '1.5', None):
            with self.subTest(value=value):
                config, _ = self.parse_text(json.dumps({'seed': value}))
                self.assertEqual(config.seed, '42')

    def parse_text(self, text: str) -> tuple[Config, str]:
        """Parse a temporary file and capture diagnostic messages."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(text, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                config = parse(path)
            return config, output.getvalue()

    def test_missing_keys_report_defaults(self) -> None:
        """Missing fields must be visible rather than silently defaulted."""
        config, output = self.parse_text('{}')
        self.assertEqual(config.lives, 3)
        self.assertEqual(config.level_max_time, 90)
        self.assertEqual(config.pacgum, 0)
        self.assertIn('lives', output)
        self.assertIn('default', output.lower())

    def test_gameplay_values_and_short_levels(self) -> None:
        """Accept evaluation times, integer seeds and pad custom levels."""
        config, output = self.parse_text(json.dumps({
            'seed': 123, 'level_max_time': 2,
            'levels': [{'level_number': 1, 'width': 7, 'height': 40}],
            'power_duration': 2.5, 'ghost_respawn_time': 1.5,
            'player_speed': 6.5, 'ghost_speed': 3.5,
        }))
        self.assertEqual(config.seed, '123')
        self.assertEqual(config.level_max_time, 2)
        self.assertEqual(len(config.levels), 10)
        self.assertEqual(config.levels[0].width, 7)
        self.assertEqual(config.power_duration, 2.5)
        self.assertEqual(config.ghost_respawn_time, 1.5)
        self.assertEqual(config.player_speed, 6.5)
        self.assertEqual(config.ghost_speed, 3.5)
        self.assertIn('levels', output)

    def test_unsafe_values_fall_back_independently(self) -> None:
        """Reject unbounded sizes, booleans and nonfinite gameplay values."""
        config, output = self.parse_text(json.dumps({
            'lives': True, 'window_width': 99999, 'window_height': -1,
            'levels': [{'level_number': 1, 'width': 41, 'height': 6}],
            'power_duration': float('nan'), 'ghost_respawn_time': -1,
            'player_speed': 1000, 'ghost_speed': 0,
            'points_per_pacgum': 17,
        }))
        defaults = Config()
        for field in ('lives', 'window_width', 'window_height', 'levels',
                      'power_duration', 'ghost_respawn_time',
                      'player_speed', 'ghost_speed'):
            self.assertEqual(getattr(config, field), getattr(defaults, field))
            self.assertIn(field, output)
        self.assertEqual(config.points_per_pacgum, 17)

    def test_comments_unknown_keys_and_hash_strings(self) -> None:
        """Whole-line comments are ignored, not hash characters in strings."""
        config, output = self.parse_text(
            '  # comment\n{\n# another\n"highscore_filename": "a#b.json",'
            ' "lives": 4, "unknown": false}\n')
        self.assertEqual(config.lives, 4)
        self.assertEqual(config.highscore_filename, 'a#b.json')
        self.assertNotIn('unknown', output)

    def test_invalid_files_never_raise(self) -> None:
        """Malformed JSON, bad roots and bad UTF-8 recover without raising."""
        for text in ('{', '[]', 'null'):
            with self.subTest(text=text):
                config, output = self.parse_text(text)
                self.assertEqual(config, Config())
                self.assertIn('default', output.lower())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'broken.json'
            path.write_bytes(b'\xff')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(parse(path), Config())
                self.assertEqual(
                    parse(path.parent / 'missing.json'),
                    Config()
                )
                self.assertEqual(parse(path.parent), Config())
                self.assertEqual(parse(path.parent / 'bad.txt'), Config())

    def test_large_pacgum_count_clamped(self) -> None:
        """Counts cannot exceed the maximum possible maze cell count."""
        config, output = self.parse_text('{"pacgum": 999999}')
        self.assertEqual(config.pacgum, 1600)
        self.assertIn('pacgum', output)
        self.assertEqual(Config().pacgum, 0)

    def test_invalid_highscore_path_and_deep_json(self) -> None:
        """Bad output paths and pathological nesting use safe defaults."""
        for name in ('', '   ', 'bad\x00path', '\ud800'):
            config, output = self.parse_text(json.dumps({
                'highscore_filename': name}))
            self.assertEqual(config.highscore_filename, 'highscores.json')
            self.assertIn('highscore_filename', output)
        config, output = self.parse_text('[' * 2000 + ']' * 2000)
        self.assertEqual(config, Config())
        self.assertIn('default', output.lower())


if __name__ == '__main__':
    unittest.main()
