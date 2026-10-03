"""Remove disposable source caches without touching vendors or build proof."""
import os
import shutil
import sys
from pathlib import Path


CACHE_NAMES = frozenset({'__pycache__', '.mypy_cache', '.pytest_cache'})
PROTECTED_NAMES = frozenset({
    '.git', '.venv', '.uv-cache', 'build', 'dist', 'extract', 'mlx-2.2',
    'vendor', 'vendors', 'venv', 'node_modules',
})


def clean_caches(root: Path) -> list[Path]:
    """Delete named caches below root, never traversing directory symlinks."""
    root = root.resolve()
    removed: list[Path] = []
    for directory, names, _ in os.walk(root, followlinks=False):
        for name in list(names):
            path = Path(directory) / name
            if path.is_symlink() or name in PROTECTED_NAMES:
                names.remove(name)
            elif name in CACHE_NAMES:
                shutil.rmtree(path)
                removed.append(path)
                names.remove(name)
    return removed


def main() -> int:
    """Clean this script's repository and report filesystem errors safely."""
    try:
        removed = clean_caches(Path(__file__).resolve().parent)
    except OSError as error:
        print(f'Cache cleanup failed: {error}', file=sys.stderr)
        return 1
    print(f'Removed {len(removed)} cache directories.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
