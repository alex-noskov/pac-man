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

### Requirements

The repository is configured for:

- Linux;
- Python **3.12 or 3.13**;
- `uv`;
- `make`;
- an X11 or XWayland graphical session required by the supplied MLX build.

Install the locked dependencies from the repository root:

```sh
make install
```

Run the game:

```sh
make run
```

The required direct command-line form is:

```sh
python3 pac-man.py config.json
```

The launcher accepts exactly one `.json` configuration path.

A different configuration file can be used with:

```sh
make run CONFIG=custom.json
```

Useful development commands:

```sh
make debug        # run through Python's pdb debugger
make lint         # flake8 + mandatory mypy checks
make lint-strict  # flake8 + mypy --strict
make clean        # remove generated caches/build files
make package      # build the standalone Linux distribution
```

Missing files, malformed configuration data, invalid field values, and other
expected input errors are handled with diagnostic messages and safe defaults
instead of an unhandled traceback.

### Controls

| Context | Keys | Action |
| --- | --- | --- |
| Main menu | Up/Down or W/S | Change selection |
| Main menu | Enter | Confirm selection |
| Gameplay | Arrow keys or WASD | Move / queue the next turn |
| Gameplay | Esc or P | Pause |
| Pause menu | Up/Down or W/S | Select Resume or Main Menu |
| Pause menu | Enter | Confirm selection |
| Pause menu | Esc or P | Resume immediately |
| Level complete | Enter | Start the next level immediately |
| Highscores / Instructions | Esc | Return to the main menu |
| Victory / Game Over | Letters, digits, Space, Backspace | Edit player name |
| Victory / Game Over | Enter | Save score and return to the main menu |
| Victory / Game Over | Esc | Return to the main menu without saving |
| Any screen | Window close button | Exit the application |

If no key is pressed on the Level Complete screen, the next level starts
automatically after three seconds.

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

Cheat actions only apply while cheat mode is enabled. Disabling cheat mode also
clears invincibility, ghost freeze, and the speed multiplier.

## Configuration

The configuration file is JSON. Whole lines whose first non-whitespace character
is `#` are ignored before JSON parsing.

Unknown keys are ignored. Missing or invalid top-level fields fall back
independently to validated parser defaults. If the complete file cannot be read or
parsed, the game continues with the full default configuration.

### Parser defaults and accepted values

| Key | Parser default | Validation / meaning |
| --- | --- | --- |
| `highscore_filename` | `highscores.json` | Non-empty UTF-8 filesystem path without NUL characters |
| `levels` | 10 predefined levels | Array of level objects; lists shorter than 10 are padded with default levels |
| `level_number` | `1` for an individual level | Non-negative integer label |
| `width` | Defined by the default level list | Integer from `7` to `40` |
| `height` | Defined by the default level list | Integer from `7` to `40` |
| `lives` | `3` | Integer from `1` to `10` |
| `pacgum` | `0` | `0` fills all eligible reachable cells; positive values request a count; values above `1600` are clamped to `1600` |
| `points_per_pacgum` | `10` | Positive integer |
| `points_per_super_pacgum` | `50` | Positive integer |
| `points_per_ghost` | `200` | Positive integer |
| `seed` | `42` | Positive integer seed in `1..2147483647`; internally stored as a string |
| `level_max_time` | `90` | Integer seconds in `1..500` |
| `window_width` | `1280` | Integer pixels in `800..3840` |
| `window_height` | `800` | Integer pixels in `600..2160` |
| `power_duration` | `8` | Finite number of seconds in `0.1..120` |
| `ghost_respawn_time` | `5` | Finite number of seconds in `0.1..120` |
| `player_speed` | `5` | Finite cells/second value in `0.1..30` |
| `ghost_speed` | `2` | Finite cells/second value in `0.1..30` |

The parser's ten default maze dimensions are:

```text
15x15
20x18
20x20
25x20
25x25
30x25
30x28
32x30
35x30
35x35
```

The supplied `config.json` intentionally overrides those parser defaults with ten
custom level definitions:

```text
14x14
19x17
19x19
24x19
24x24
29x24
29x27
31x29
34x29
34x34
```

Its `level_number` values are `0..9`. `level_number` is a validated level label;
actual progression and the HUD use the level's position in the configured list.

The three scoring values have no arbitrary application-level upper limit. They
must simply be positive integers, and Python integer arithmetic is used for the
accumulated score.

If a requested window is larger than the available display, the MLX wrapper caps
the actual window to the detected screen size with a small margin.

## Highscore

`HighscoreStore` keeps a persistent JSON Top 10 table. Names are limited to 1-10
ASCII letters, digits, or spaces, and scores must be non-negative integers.
Malformed entries are ignored instead of crashing the application.

After victory or game over, the player can enter a name and save the final score.
Scores are sorted in descending order. Saving uses a temporary file followed by
atomic replacement so that an existing highscore file is preserved if writing
fails.

JSON was chosen because the highscore data is small, human-readable, portable,
and requires no external database while still allowing validation and atomic
persistence.

## Maze Generation

The project does **not** implement its own maze generator.

`src/maze.py` imports and adapts the assigned `mazegenerator` package directly:

```python
MazeGenerator((width, height), perfect=False, seed=int(seed))
```

The assigned package is used as supplied and is not modified.

After generation, the adapter validates the rectangular dimensions, wall-mask
values, closed outer boundaries, and reciprocal walls between neighboring cells.

Pac-Man is placed on the reachable cell nearest the geometric center of the maze.
The four ghost spawn positions and the four power-pellet positions are chosen from
reachable cells nearest the four corners. Normal pacgums are placed only in the
player's reachable component, excluding the player start and power-pellet cells.

The first level uses the configured fixed seed. Every later level generates a new
positive random seed.

If maze generation or validation fails, gameplay enters a recoverable error state
instead of raising an uncaught exception.

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
over between levels. A level completes when all normal pacgums have been eaten;
power pellets remain optional collectibles. The game ends on the final completed
level, when all lives are lost, or when the level timer expires.

The Level Complete screen advances automatically after three seconds, while Enter
allows immediate continuation.

The UI uses MLX image layers: the maze can remain cached while actors, pellets, HUD,
and overlays are redrawn independently. UI boxes use percentage-based geometry,
and bitmap text is fitted to each box after its relative padding is applied.

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

This separation keeps gameplay logic independent of the graphical layer.

## Project Management

The project was managed by dividing work by subsystem, tracking milestones and
actual progress, recording important design decisions and risks, documenting bugs
and fixes, and validating the finished features against an acceptance plan.

Detailed project-management records are available in
[`project_management/`](project_management/README.md).

## Packaging

The repository contains `package.py` at its root. Run:

```sh
make package
```

Before building, the script validates these required inputs:

- `config.json`;
- `INSTRUCTIONS.txt`;
- `mazegenerator-2.1.0-py3-none-any.whl`;
- `mlx-2.2-py3-none-any.whl`;
- `MLX-LICENSE.txt`.

It then runs PyInstaller in `onedir` mode and creates:

```text
dist/pac-man/
```

After a successful build, the runtime support files copied beside the executable
are:

```text
config.json
INSTRUCTIONS.txt
mazegenerator-2.1.0-py3-none-any.whl
MLX-LICENSE.txt
```

The MLX wheel remains a source/build dependency; its installed runtime is collected
by PyInstaller into the standalone distribution.

The complete `dist/pac-man/` directory must stay together. Start the packaged game
with:

```sh
./pac-man config.json
```

No Python installation is required to run the completed PyInstaller distribution.
`INSTRUCTIONS.txt` provides minimal in-package controls, options, and configuration
information.

For evaluation, the verified packaged build must also be made available from an
accepted public gaming platform such as Itch.io or Steam; a free unlisted/private
build is sufficient.

## Resources

- Pac-Man subject v1.5 - authoritative project specification.
- Supplied `mlx-2.2-py3-none-any.whl` package and `MLX-LICENSE.txt`.
- Supplied `mazegenerator` 2.1.0 package interface.
- [Python documentation](https://docs.python.org/3/).
- [Pydantic documentation](https://docs.pydantic.dev/).
- [mypy documentation](https://mypy.readthedocs.io/).
- [PyInstaller documentation](https://pyinstaller.org/).

AI assistance was used during the completion/review stage to compare the project
against the subject, analyze existing code and runtime failures, help implement and
refactor gameplay/persistence/native-resource handling, prepare verification
scenarios, review packaging, and draft technical documentation. Generated
suggestions were reviewed against the source code and manually validated; the
project owners remain responsible for understanding and defending the final
implementation.
