"""Regenerate the local Linux onedir distribution with PyInstaller."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


GENERATOR_WHEEL = "mazegenerator-2.1.0-py3-none-any.whl"
MLX_WHEEL = "mlx-2.2-py3-none-any.whl"
MLX_LICENSE = "MLX-LICENSE.txt"


def build_inputs(root: Path) -> list[Path]:
    """Return files required to reproduce and package the game."""
    return [
        root / "config.json",
        root / "INSTRUCTIONS.txt",
        root / GENERATOR_WHEEL,
        root / MLX_WHEEL,
        root / MLX_LICENSE,
    ]


def validate_build_inputs(files: list[Path]) -> None:
    """Ensure every required packaging input exists before building."""
    for source in files:
        if not source.is_file():
            raise FileNotFoundError(
                f"Missing packaging input: {source}"
            )


def support_files(root: Path) -> list[tuple[Path, str]]:
    """Return files that must accompany the packaged executable."""
    return [
        (root / "config.json", "config.json"),
        (root / "INSTRUCTIONS.txt", "INSTRUCTIONS.txt"),
        (root / GENERATOR_WHEEL, GENERATOR_WHEEL),
        (root / MLX_LICENSE, MLX_LICENSE),
    ]


def copy_support_files(
    files: list[tuple[Path, str]],
    destination: Path,
) -> None:
    """Copy runtime configuration, instructions, and vendor notices."""
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in files:
        shutil.copy2(source, destination / name)


def build_command(root: Path) -> list[str]:
    """Return an isolated PyInstaller command for the project."""
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "pac-man",
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build" / "pyinstaller"),
        "--specpath",
        str(root / "build" / "pyinstaller"),
        "--paths",
        str(root),
        "--collect-all",
        "mlx",
        "--collect-all",
        "mazegenerator",
        "--collect-all",
        "pydantic",
        "--exclude-module",
        "pygame",
        str(root / "pac-man.py"),
    ]


def main() -> int:
    """Build the distribution and report failures without a traceback."""
    root = Path(__file__).resolve().parent
    destination = root / "dist" / "pac-man"
    inputs = build_inputs(root)
    files = support_files(root)

    try:
        validate_build_inputs(inputs)

        environment = dict(os.environ)
        environment["PYINSTALLER_CONFIG_DIR"] = str(
            root / ".uv-cache" / "pyinstaller"
        )

        subprocess.run(
            build_command(root),
            cwd=root,
            check=True,
            env=environment,
        )

        copy_support_files(files, destination)

    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return 1

    print(f"Standalone distribution ready: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
