# Linux standalone packaging

## Regenerate locally

From the repository root, use `make install`, then `make package` (or
`UV_CACHE_DIR=.uv-cache uv run python package.py`). The root `package.py`
uses the current interpreter's PyInstaller and builds an **onedir** distribution:

```sh
cd dist/pac-man
./pac-man config.json
```

Copy/archive the entire `dist/pac-man/` directory, including `_internal/`.
The executable accepts exactly one JSON configuration filename. It includes
Python and does not require a user Python installation. It is a Linux build,
not a Windows/macOS build. Build on the oldest Linux baseline you intend to
support: the host's glibc and native-library requirements remain relevant.
A graphical X11 session and compatible system X11/OpenGL libraries are needed.
A successful CLI smoke test alone does not establish playable GUI behavior.

PyInstaller explicitly collects `mlx` (including the ctypes-loaded
`_internal/mlx/libmlx.so`), `mazegenerator`, and `pydantic`. Unused `pygame`
is excluded. The supplied generator implementation is not edited. The
unmodified `mazegenerator-2.1.0-py3-none-any.whl`, configuration,
`INSTRUCTIONS.txt`, `MLX-LICENSE.txt` (copied byte-for-byte from the vendor
LICENSE), and `README.md` when present are copied beside the executable.
MLX's original LICENSE is never altered.

Build output and generated spec live under `build/pyinstaller/`; runtime
output lives under `dist/`. PyInstaller's cache is explicitly directed to
`.uv-cache/pyinstaller/`, not a machine-wide cache. Rebuilding replaces the
existing `dist/pac-man` PyInstaller output. Packaging reports a missing
required support file or a failed bundler with a nonzero exit code.

## Verification

Fast regression tests do not invoke the expensive actual bundler:

```sh
uv run python -m unittest tests.test_packaging tests.test_clean -v
```

After regenerating, execute `dist/pac-man/pac-man` without arguments: expected
exit status **2**, a usage diagnostic, and no Python traceback. Also check
that `_internal/mlx/libmlx.so` exists, compare the included vendor wheel and
license against their original files, and test a valid configuration in an
actual graphical session before release. Highscores need a writable configured
location. Controls, cheat options, and configuration guidance are in the
included `INSTRUCTIONS.txt`.

## Cache cleanup

`make clean` (or `uv run python clean.py`) removes only `__pycache__`,
`.mypy_cache`, and `.pytest_cache` directories in the source tree. It skips
symlinks and does not traverse virtual environments, `.uv-cache`, `.git`,
`build`, `dist`, `extract`, `mlx-2.2`, or vendor directories. It preserves
build/QA evidence and installed dependencies.

## Public-platform delivery still requires an owner

This script builds locally; it does not upload or claim deployment. An account
owner must create a free restricted/unlisted project on Itch.io (or equivalent),
archive the complete distribution, upload it as a Linux download, include launch
instructions, and test installation/download plus gameplay from that platform.
Record the actual platform URL and release evidence in project-management
records after publishing. No credentials or account access are required for
local packaging; public-platform delivery remains a separate acceptance step.
