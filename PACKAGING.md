# Packaging

The project includes `package.py` and the `make package` target to regenerate a
standalone Linux distribution for release and peer review.

## Build

From the repository root:

```sh
make install
make package
```

`make package` runs `package.py`, which builds a PyInstaller **onedir**
distribution in:

```text
dist/pac-man/
```

The complete directory must be kept together. In particular, do not separate
the `pac-man` executable from its `_internal/` directory.

## Run the packaged game

From the generated distribution:

```sh
cd dist/pac-man
./pac-man config.json
```

The executable requires exactly one JSON configuration path, just like the
source entry point. A separate Python installation is not required.

The current package is a Linux build and requires a graphical X11 environment
with compatible system X11/OpenGL libraries.

## Files included beside the executable

The packaging script copies the following support files into `dist/pac-man/`:

- `config.json`
- `INSTRUCTIONS.txt`
- `README.md` when present
- `mazegenerator-2.1.0-py3-none-any.whl`
- `MLX-LICENSE.txt`

The maze-generator wheel is included unchanged. PyInstaller also collects the
runtime code required by `mlx`, `mazegenerator`, and `pydantic`.

## Verification before release

Run the normal project checks first:

```sh
make clean
make test
make lint
make lint-strict
make package
```

Then verify the generated distribution itself:

```sh
cd dist/pac-man
./pac-man config.json
```

Check at least the main menu, gameplay, pause/resume, level completion,
game-over/victory flow, name entry, and persistent highscores.

Also verify that:

- `_internal/` is present beside the executable;
- `config.json` and `INSTRUCTIONS.txt` are present;
- the configured highscore location is writable;
- launching with an invalid argument count fails cleanly without a Python traceback.

## Public-platform release

Local packaging is only the build step. The subject also requires a functional
build to be made available through a public gaming platform such as Itch.io or
Steam; an unlisted/private free page is acceptable if supported by the chosen
platform.

For release, archive or upload the **entire** `dist/pac-man/` directory, provide
the launch instruction:

```sh
./pac-man config.json
```

and test the downloaded platform build rather than relying only on the local
copy.

## Generated files

PyInstaller build artifacts are written under:

```text
build/pyinstaller/
dist/pac-man/
```

These are generated outputs and should not be treated as source files.
