"""Regenerate the local Linux onedir distribution with PyInstaller."""
import os
import shutil
import subprocess
import sys
from pathlib import Path


GENERATOR_WHEEL = 'mazegenerator-2.1.0-py3-none-any.whl'
MLX_LICENSE = Path('mlx-2.2/src/mlx_CLXV-2.2/mlx_CLXV/LICENSE')


def copy_support_files(
    root: Path,
    destination: Path,
) -> None:
    """Validate inputs then copy user instructions and unchanged vendors."""
    files = [(root / name, name) for name in
             ('config.json', 'INSTRUCTIONS.txt', GENERATOR_WHEEL)]
    files.append((root / MLX_LICENSE, 'MLX-LICENSE.txt'))
    if (root / 'README.md').is_file():
        files.append((root / 'README.md', 'README.md'))
    for source, _ in files:
        if not source.is_file():
            raise FileNotFoundError(f'Missing packaging input: {source}')
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in files:
        shutil.copy2(source, destination / name)


def build_command(root: Path) -> list[str]:
    """Return an isolated build command rooted in the source worktree."""
    return [
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onedir', '--name', 'pac-man',
        '--distpath', str(root / 'dist'),
        '--workpath', str(root / 'build' / 'pyinstaller'),
        '--specpath', str(root / 'build' / 'pyinstaller'),
        '--paths', str(root),
        '--collect-all', 'mlx', '--collect-all', 'mazegenerator',
        '--collect-all', 'pydantic', '--exclude-module', 'pygame',
        str(root / 'pac-man.py'),
    ]


def main() -> int:
    """Build the distribution, reporting failures without a traceback."""
    root = Path(__file__).resolve().parent
    destination = root / 'dist' / 'pac-man'
    try:
        copy_support_files(root, destination)
        environment = dict(os.environ)
        environment['PYINSTALLER_CONFIG_DIR'] = str(
            root / '.uv-cache' / 'pyinstaller'
        )
        subprocess.run(build_command(root), cwd=root, check=True,
                       env=environment)
        copy_support_files(root, destination)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'Packaging failed: {error}', file=sys.stderr)
        return 1
    print(f'Standalone distribution ready: {destination}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
