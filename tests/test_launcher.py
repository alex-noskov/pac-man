"""Command-line contract for the assignment's root launcher."""
import subprocess
import sys
import unittest
from pathlib import Path


class LauncherTests(unittest.TestCase):
    """Invalid invocation must never initialize graphics or traceback."""

    def test_root_launcher_reports_wrong_argument_count(self) -> None:
        """The mandated pac-man.py entrypoint accepts exactly one path."""
        root = Path(__file__).resolve().parents[1]
        for args in ([], ['a.json', 'b.json']):
            result = subprocess.run([sys.executable, 'pac-man.py', *args],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Usage: python3 pac-man.py <config.json>',
                          result.stdout + result.stderr)
            self.assertNotIn('Traceback', result.stdout + result.stderr)
