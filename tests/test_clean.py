"""Regression coverage for bounded repository cache cleanup."""
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class CleanTests(unittest.TestCase):
    """Only disposable caches in owned source directories may be removed."""

    def test_removes_only_named_caches(self) -> None:
        """Leave environments, vendor trees and build evidence untouched."""
        self.assertTrue(Path('clean.py').is_file(), 'clean.py is missing')
        cleaner = importlib.import_module('clean')
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            removable = [root / 'src' / '__pycache__',
                         root / '.mypy_cache', root / '.pytest_cache']
            protected = [root / name / '__pycache__' for name in
                         ('.venv', '.uv-cache', 'build', 'dist', 'extract',
                          'mlx-2.2', '.git', 'vendor')]
            for path in removable + protected:
                path.mkdir(parents=True)
                (path / 'evidence').write_text('keep unless cache')
            cleaner.clean_caches(root)
            for path in removable:
                self.assertFalse(path.exists())
            for path in protected:
                self.assertTrue((path / 'evidence').exists())

    def test_symlinks_never_escape_cleanup_root(self) -> None:
        """Skip symlinked directories, caches, and links inside caches."""
        cleaner = importlib.import_module('clean')
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base = Path(directory)
            root = base / 'repository'
            external = base / 'external'
            root.mkdir()
            external.mkdir()
            evidence = external / 'evidence'
            evidence.write_text('must survive')
            (root / 'linked_source').symlink_to(external, True)
            (root / '.mypy_cache').symlink_to(external, True)
            cache = root / '__pycache__'
            cache.mkdir()
            (cache / 'external').symlink_to(external, True)
            cleaner.clean_caches(root)
            self.assertEqual(evidence.read_text(), 'must survive')
            self.assertTrue((root / 'linked_source').is_symlink())
            self.assertTrue((root / '.mypy_cache').is_symlink())
            self.assertFalse(cache.exists())

    def test_named_file_is_not_removed(self) -> None:
        """A non-directory named like a cache is not disposable."""
        cleaner = importlib.import_module('clean')
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            file = root / '__pycache__'
            file.write_text('not a directory')
            cleaner.clean_caches(root)
            self.assertTrue(file.is_file())

    def test_main_reports_errors_without_traceback(self) -> None:
        """Filesystem permission failures have a nonzero clean exit."""
        cleaner = importlib.import_module('clean')
        with patch('clean.clean_caches',
                   side_effect=PermissionError('denied')):
            with patch('sys.stderr') as error:
                self.assertEqual(cleaner.main(), 1)
                self.assertTrue(error.write.called)


if __name__ == '__main__':
    unittest.main()
