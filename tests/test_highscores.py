"""Regression tests for persistent top-ten scores."""
from pathlib import Path
import tempfile
import unittest

from unittest.mock import patch

from src.highscores import HighscoreStore


class HighscoreTests(unittest.TestCase):
    """Exercise validation and real disk persistence."""

    def test_round_trip_top_ten(self) -> None:
        """Save scores and reload the sorted top ten from disk."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scores.json'
            store = HighscoreStore(path)
            store.load()
            self.assertEqual(store.entries, [])
            for score in range(12):
                self.assertTrue(store.add(f'Player {score}', score))
            self.assertEqual(len(store.entries), 10)
            self.assertEqual(store.entries[0],
                             {'name': 'Player 11', 'score': 11})
            self.assertTrue(store.save())
            loaded = HighscoreStore(path)
            loaded.load()
            self.assertEqual(loaded.entries, store.entries)
            self.assertEqual(loaded.error, '')

    def test_invalid_entries_leave_table_unchanged(self) -> None:
        """Only nonempty ASCII names and genuine nonnegative ints qualify."""
        with tempfile.TemporaryDirectory() as directory:
            store = HighscoreStore(Path(directory) / 'scores.json')
            self.assertTrue(store.add('Valid 123', 0))
            before = list(store.entries)
            for name in ('', '   ', 'ElevenChars', 'René', 'A_B', 'x\n',
                         '\ud800'):
                with self.subTest(name=name):
                    self.assertFalse(store.add(name, 1))
                    self.assertTrue(store.error)
                    self.assertEqual(store.entries, before)
            for score in (-1, True, False, 1.5, '3', None):
                with self.subTest(score=score):
                    self.assertFalse(store.add('Valid', score))  # type: ignore
                    self.assertEqual(store.entries, before)
            self.assertTrue(store.add('Valid', 1))
            self.assertEqual(store.error, '')

    def test_corrupt_files_and_invalid_rows(self) -> None:
        """Recover valid rows and report corrupt files without tracebacks."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scores.json'
            store = HighscoreStore(path)
            for content in (b'{', b'null', b'{}', b'\xff'):
                path.write_bytes(content)
                store.load()
                self.assertEqual(store.entries, [])
                self.assertTrue(store.error)
            path.write_text(
                '[{"name":"Good","score":5},'
                '{"name":"Bad","score":true},null,{},'
                '{"name":"Best","score":20}]', encoding='utf-8')
            store.load()
            self.assertEqual(store.entries, [
                {'name': 'Best', 'score': 20}, {'name': 'Good', 'score': 5}])
            self.assertTrue(store.error)

    def test_atomic_save_failure_preserves_old_file(self) -> None:
        """Failed replacement must leave the old scores and no temp files."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scores.json'
            store = HighscoreStore(path)
            store.add('Old', 1)
            self.assertTrue(store.save())
            original = path.read_bytes()
            store.add('New', 2)
            with patch('os.replace',
                       side_effect=OSError('disk failure')):
                self.assertFalse(store.save())
            self.assertTrue(store.error)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(path.parent.iterdir()), [path])
            self.assertTrue(store.save())
            self.assertEqual(store.error, '')

    def test_io_errors_are_reported(self) -> None:
        """Directory paths and missing parent directories fail gracefully."""
        with tempfile.TemporaryDirectory() as directory:
            store = HighscoreStore(directory)
            store.load()
            self.assertEqual(store.entries, [])
            self.assertTrue(store.error)
            self.assertFalse(store.save())
            self.assertTrue(store.error)
            missing = HighscoreStore(Path(directory) / 'missing' / 'file.json')
            self.assertFalse(missing.save())
            self.assertTrue(missing.error)


if __name__ == '__main__':
    unittest.main()
