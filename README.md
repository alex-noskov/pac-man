*This project has been created as part of the 42 curriculum by vpolikha, anoskov.*

# Pac-Man

## Description

A complete Pac-Man-style game written in Python with the supplied **MLX 2.2**
graphics library and the assigned **A-Maze-ing / `mazegenerator` 2.1.0** package.

The game contains ten generated levels, Pac-Man movement through maze corridors,
normal and power pellets, four autonomous ghosts, scoring, lives, a level timer,
pause and evaluation cheats, victory/game-over flows, and persistent Top 10
highscores. The first maze is generated from a fixed seed; later levels use fresh
random seeds.

## Instructions

The project currently targets **Python 3.12 or 3.13 on Linux**. A working X11 or
XWayland graphical session is required by the supplied MLX build.

Install dependencies and run the game from the repository root:

```sh
make install
make run
```

The required command-line form is:

```sh
python3 pac-man.py config.json
```

A different configuration can be used with:

```sh
make run CONFIG=custom.json
```

Useful development commands:

```sh
make debug        # run with pdb
make test         # run the unittest suite
make lint         # flake8 + mypy checks required by the subject
make lint-strict  # stricter mypy validation
make validate     # tests + lint
make clean        # remove generated caches
make package      # build the standalone Linux package
```

The launcher accepts exactly one `.json` configuration file. Invalid or missing
configuration values are handled with clear messages and safe defaults rather than
an unhandled traceback.

### Controls

| Context | Keys | Action |
| --- | --- | --- |
| Menus | Up/Down or W/S, Enter | Select and confirm |
| Gameplay | Arrow keys or WASD | Move / queue a turn |
| Gameplay | Esc or P | Pause |
| Pause | Up/Down, Enter | Resume or return to main menu |
| Level complete | Enter | Start the next level |
| Other screens | Esc | Return to main menu |
| Victory / Game Over | Letters, digits, Space, Backspace | Edit player name |
| Victory / Game Over | Enter | Save score and return to menu |

### Evaluation cheats

Press **C** during gameplay to enable or disable cheat controls.

| Key | Effect |
| --- | --- |
| I | Toggle invincibility |
| N | Complete the current level |
| F | Freeze / unfreeze ghosts |
| L | Add one life |
| B | Toggle double player speed |
| V | Activate the normal power-pellet state |

Disabling cheat mode also clears invincibility, ghost freeze, and the speed
multiplier.

## Configuration

The configuration is JSON and also accepts whole comment lines beginning with `#`.
Unknown keys are ignored. Missing or invalid fields fall back independently to
validated defaults.

| Key | Default | Meaning |
| --- | --- | --- |
| `highscore_filename` | `highscores.json` | Persistent score file |
| `levels` | 10 levels | Maze definitions; short lists are padded to ten levels |
| `width`, `height` | 15x15 up to 35x35 | Maze dimensions, accepted range 7..40 |
| `level_number` | `1` | Optional non-negative level label |
| `lives` | `3` | Starting lives |
| `pacgum` | `0` | `0` fills all eligible reachable corridors; positive values request a count |
| `points_per_pacgum` | `10` | Score for a normal pellet |
| `points_per_super_pacgum` | `50` | Score for a power pellet |
| `points_per_ghost` | `200` | Score for an edible ghost |
| `seed` | `42` | Fixed positive seed for the first level |
| `level_max_time` | `90` | Level time limit in seconds |
| `window_width` | `1280` | Requested window width |
| `window_height` | `800` | Requested window height |
| `power_duration` | `8` | Edible-ghost duration in seconds |
| `ghost_respawn_time` | `5` | Delay before an eaten ghost returns |
| `player_speed` | `5` | Player speed in cells per second |
| `ghost_speed` | `2` | Shared ghost speed in cells per second |

The supplied `config.json` contains ten custom maze sizes from `14x14` to `34x34`
and uses the gameplay values shown above. If the requested window is larger than
the available display, the MLX wrapper caps it to the detected screen size with a
small margin.

## Highscore

`HighscoreStore` keeps a persistent JSON Top 10 table. Names are limited to 1-10
ASCII letters, digits, or spaces, and scores must be non-negative integers.
Malformed entries are ignored instead of crashing the application.

After victory or game over, the player can enter a name and save the final score.
Scores are sorted in descending order. Saving uses a temporary file followed by
atomic replacement so that an existing highscore file is preserved if writing
fails.

## Maze Generation

The project does not implement its own maze generator. `src/maze.py` adapts the
assigned package directly:

```python
MazeGenerator((width, height), perfect=False, seed=seed)
```

The returned maze is validated before gameplay. Pac-Man is placed at the nearest
reachable cell to the maze center. Four ghosts and four power pellets use reachable
corner positions, and normal pellets are placed only in the player's reachable
component.

The first level uses the configured fixed seed. Subsequent levels use fresh random
seeds. The assigned generator package is used as supplied and is not modified.

## Implementation

Gameplay rules and state are concentrated in `GameSession`, independently of the
window code. Actor positions are stored in maze-cell coordinates using floating
point values; rendering converts them to pixels. Movement is based on elapsed time,
not frame count, and turns are resolved at cell centers.

The simulation uses short time steps and swept collision checks so fast actors
cannot pass through each other between frames. Normal ghosts choose a legal
neighbor that locally reduces Manhattan distance to Pac-Man; while edible they
choose a neighbor that increases it. Randomness only resolves equal choices.

Pause freezes gameplay movement and timers. A lost life respawns actors without
resetting the current score or collected pellets. Score and remaining lives carry
over between levels. The game ends on the final completed level, when all lives are
lost, or when the level timer expires.

The UI uses MLX image layers: the maze can remain cached while actors, pellets, HUD,
and overlays are redrawn independently. Fixed bitmap-font scales and UI colors are
kept in `src/ui/layout.py`.

## General Software Architecture

```text
pac-man.py
  -> src.parsing.parse / Config
  -> src.app.App
       -> src/ui/screen_*.py
       -> src.session.GameSession
            -> src.maze.Maze
                 -> assigned MazeGenerator
       -> src.highscores.HighscoreStore
       -> src/ui/graphics.Graphics
            -> src/ui/mlx_wrapper.MlxWrapper
                 -> supplied MLX library
```

Main responsibilities:

- `src/app.py` - application lifecycle and screen transitions.
- `src/parsing.py` - commented JSON parsing, validation, and safe defaults.
- `src/session.py` - movement, ghosts, collisions, scoring, lives, timers, cheats,
  and level progression.
- `src/maze.py` - validated adapter around the assigned maze generator.
- `src/highscores.py` - persistent validated Top 10 storage.
- `src/ui/` - screens, input events, layout, bitmap text, rendering, and the MLX
  boundary.

This separation keeps gameplay testable without opening a graphical window.

## Project Management

Project planning, progress, design decisions, risks, team responsibilities,
bug tracking, and acceptance testing are documented in
[`project_management/`](project_management/README.md).

## Packaging

`make package` builds a standalone Linux distribution with PyInstaller under
`dist/pac-man/`. The packaged directory includes the executable and required
support files. Detailed build and verification instructions are in
[`PACKAGING.md`](PACKAGING.md).

Publishing the verified build to the required public gaming platform is a separate
release step and should be completed by the project owners before evaluation.

## Resources

- Pac-Man subject v1.5 - authoritative project specification.
- Supplied MLX 2.2 library and its documentation/source.
- Supplied `mazegenerator` 2.1.0 package interface.
- [Python documentation](https://docs.python.org/3/).
- [Python `unittest`](https://docs.python.org/3/library/unittest.html).
- [Pydantic documentation](https://docs.pydantic.dev/).
- [mypy documentation](https://mypy.readthedocs.io/).
- [PyInstaller documentation](https://pyinstaller.org/).

AI assistance was used during the completion/review stage to compare the project
against the subject, analyze existing code and runtime failures, help implement and
refactor gameplay/persistence/native-resource handling, design regression tests,
prepare packaging, and draft technical documentation. Generated suggestions were
reviewed against the source code and validated with automated tests and native runs;
the project owners remain responsible for understanding and defending the final
implementation.
