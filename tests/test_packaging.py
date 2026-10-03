"""Fast packaging contract tests, without running PyInstaller."""
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import subprocess


class PackagingTests(unittest.TestCase):
    """Check the standalone build command and distribution contents."""

    def test_build_command_collects_native_runtime(self) -> None:
        """Collect ctypes MLX and generator dependencies, excluding pygame."""
        self.assertTrue(Path('package.py').is_file(), 'package.py is missing')
        packaging = importlib.import_module('package')
        root = Path('/example/repository')
        command = packaging.build_command(root)
        self.assertEqual(command[:3], [sys.executable, '-m', 'PyInstaller'])
        self.assertIn('--onedir', command)
        self.assertEqual(command.count('--collect-all'), 3)
        for name in ('mlx', 'mazegenerator', 'pydantic'):
            self.assertIn(name, command)
        self.assertIn('--exclude-module', command)
        self.assertIn('pygame', command)
        self.assertIn(str(root / 'pac-man.py'), command)
        self.assertIn(str(root / 'dist'), command)

    def test_support_files_are_copied_without_modification(self) -> None:
        """Bundle configuration, instructions, license and assigned wheel."""
        packaging = importlib.import_module('package')
        self.assertTrue(hasattr(packaging, 'copy_support_files'))
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            destination = root / 'dist' / 'pac-man'
            license_path = root / packaging.MLX_LICENSE
            license_path.parent.mkdir(parents=True)
            license_path.write_bytes(b'vendor license\n')
            files = ('config.json', 'INSTRUCTIONS.txt', 'README.md',
                     packaging.GENERATOR_WHEEL)
            for name in files:
                (root / name).write_bytes(name.encode())
            packaging.copy_support_files(root, destination)
            for name in files:
                self.assertEqual((destination / name).read_bytes(),
                                 (root / name).read_bytes())
            self.assertEqual((destination / 'MLX-LICENSE.txt').read_bytes(),
                             license_path.read_bytes())

    def test_missing_required_support_file_is_clear(self) -> None:
        """A missing mandatory input fails before partial support copying."""
        packaging = importlib.import_module('package')
        self.assertTrue(hasattr(packaging, 'copy_support_files'))
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FileNotFoundError, 'config.json'):
                packaging.copy_support_files(root, root / 'dist')
            self.assertFalse((root / 'dist').exists())

    def test_build_failure_returns_clean_error(self) -> None:
        """A failed bundler is surfaced without an unhandled exception."""
        packaging = importlib.import_module('package')
        self.assertTrue(hasattr(packaging, 'main'))
        with patch('package.copy_support_files'), patch(
            'package.subprocess.run',
            side_effect=subprocess.CalledProcessError(7, ['PyInstaller']),
        ), patch('sys.stderr') as error:
            self.assertEqual(packaging.main(), 1)
            self.assertTrue(error.write.called)

    def test_build_cache_stays_in_worktree(self) -> None:
        """PyInstaller must not write to the user's global cache directory."""
        packaging = importlib.import_module('package')
        with patch('package.copy_support_files'), patch(
            'package.subprocess.run',
        ) as runner, patch('sys.stdout'):
            self.assertEqual(packaging.main(), 0)
        environment = runner.call_args.kwargs.get('env', {})
        assert packaging.__file__ is not None
        root = Path(packaging.__file__).resolve().parent
        self.assertEqual(environment.get('PYINSTALLER_CONFIG_DIR'),
                         str(root / '.uv-cache' / 'pyinstaller'))


if __name__ == '__main__':
    unittest.main()
