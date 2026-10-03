"""Persistent top-ten highscore storage for the game UI."""
import json
import os
import re
import tempfile
from pathlib import Path
from typing import TypedDict


class HighscoreEntry(TypedDict):
    """A JSON-compatible player name and score."""

    name: str
    score: int


class HighscoreStore:
    """Maintain ranked entries, exposing recoverable errors to the UI."""

    def __init__(self, path: Path | str) -> None:
        """Set the storage path without performing implicit disk writes."""
        self.path = Path(path)
        self.entries: list[HighscoreEntry] = []
        self.error = ''

    def load(self) -> None:
        """Load existing scores, treating a missing file as an empty table."""
        self.error = ''
        self.entries = []
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                raise ValueError('Highscores must be a JSON array')
            for row in data:
                if isinstance(row, dict):
                    entry = self._validate(row.get('name'), row.get('score'))
                    if entry is not None:
                        self.entries.append(entry)
                        continue
                self.error = 'Invalid highscore entries were ignored.'
            self._rank()
        except FileNotFoundError:
            pass
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            self.error = f'Could not load highscores: {error}'

    @staticmethod
    def _validate(name: object, score: object) -> HighscoreEntry | None:
        """Return a clean entry only when both values meet the subject."""
        if (not isinstance(name, str) or not name.strip()
                or re.fullmatch(r'[A-Za-z0-9 ]{1,10}', name) is None):
            return None
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            return None
        return {'name': name, 'score': score}

    def _rank(self) -> None:
        """Retain ten highest entries with stable ordering for equal scores."""
        self.entries.sort(key=lambda entry: entry['score'], reverse=True)
        self.entries = self.entries[:10]

    def add(self, name: str, score: int) -> bool:
        """Insert a score and retain the top ten in descending order."""
        self.error = ''
        entry = self._validate(name, score)
        if entry is None:
            self.error = ('Name must be 1-10 ASCII letters, digits or spaces; '
                          'score must be a nonnegative integer.')
            return False
        self.entries.append(entry)
        self._rank()
        return True

    def save(self) -> bool:
        """Atomically replace the table, preserving the old file on failure."""
        self.error = ''
        temporary: Path | None = None
        try:
            payload = json.dumps(self.entries, indent=2) + '\n'
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=self.path.parent,
                prefix=f'.{self.path.name}.', suffix='.tmp', delete=False,
            ) as file:
                temporary = Path(file.name)
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
            return True
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            self.error = f'Could not save highscores: {error}'
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
