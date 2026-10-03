*This project has been created as part of the 42 curriculum by <login1>, <login2>.*

# Pac-Man

## Description

An object-oriented Pac-Man game using the supplied MLX 2.2 graphics library and
assigned `mazegenerator` 2.1.0 package. Play through at least ten generated mazes,
collect dots and corner power pellets, evade four ghosts, and save your final
score. The first maze is reproducible; subsequent levels use fresh random seeds.

The curriculum login placeholders above must be replaced by the owners' actual
42 logins before submission. Git author names are not proof of curriculum logins.

## Instructions

The supported project environment is Python 3.12 or 3.13 on Linux with a working
X11/XWayland display and the native runtime dependencies needed by the supplied
MLX wheel. No alternate graphical backend is used by the launcher.

```sh
make install                  # uv sync --frozen, local .venv
make run                      # python pac-man.py config.json
make run CONFIG=custom.json
uv run python pac-man.py config.json
make debug                    # pdb with the same config argument
make test                     # display-independent unittest suite
make lint                     # required flake8 and mypy checks
make validate                 # tests and lint
make clean                    # bounded removal of generated caches
make package                  # standalone Linux build; see PACKAGING.md
```

Exactly one configuration filename is required by `pac-man.py`. Invalid command
argument counts exit with a usage message; recoverable config errors print clear
warnings and use defaults. Native startup/callback errors are reported without a
Python traceback by the root launcher. Run from a writable directory to save
scores. The MLX wheel is supplied rather than rebuilt or modified by this project.

### Controls

| Context | Key | Action |
| --- | --- | --- |
| Main menu | Up/Down (W/S), Enter | Select and activate Play, Highscores, Instructions, Exit |
| Gameplay | Arrows or WASD | Queue movement/turns through corridors |
| Gameplay | Escape or P | Pause |
| Pause | Up/Down, Enter | Resume or return to the main menu |
| Pause | Escape or P | Resume immediately |
| Level complete | Enter | Next level, or victory after the final level |
| Secondary screens | Escape | Return to menu |
| Win/loss | Letters, digits, Space, Backspace | Enter/edit a name, maximum ten ASCII characters |
| Win/loss | Enter | Save the score and return to menu; retry if saving fails |
| Any screen | Window close | Exit and release native resources |

### Evaluation cheats

Press **C** during gameplay to enable/disable cheat controls. The HUD shows when
cheats are enabled and the invincibility/freeze flags. Disabling cheat mode resets
invincibility, freeze, and the speed multiplier; earned score/lives are retained.

| Key | Effect |
| --- | --- |
| I | Toggle invincibility |
| N | Finish this level without adding fabricated points |
| F | Toggle ghost movement freeze |
| L | Add one life |
| B | Toggle double player speed |
| V | Activate the ordinary timed edible-ghost state |

To test victory quickly: C, I, then N and Enter for each level. To test normal
collisions, start a new game (all cheats reset) or turn cheat mode off. To test
edible collisions, C and V; ghost disappearance and delayed corner respawn remain
part of the actual simulation. Cheats do not disable the level timer.

## Configuration

The file is JSON with optional whole lines beginning with `#`, including indented
comment lines. Hashes inside JSON strings are preserved. Unknown keys are ignored.
Missing/invalid fields are reported and replaced independently with safe defaults.
The sample `config.json` intentionally retains custom dimensions, point values,
seed 41 and a 499-second timer; it is not a dump of the defaults below.

| Key | Default | Accepted values/meaning |
| --- | --- | --- |
| `highscore_filename` | `highscores.json` | Nonempty filesystem path, relative to launch working directory |
| `levels` | Ten levels, 15x15 through 35x35 | List of objects with `width`, `height`, optional `level_number`; shorter lists are padded to ten |
| `width`, `height` within a level | See `DEFAULT_LEVELS` in `src/parsing.py` | Integers/numeric integer strings in 7..40 |
| `level_number` | 1 when omitted | Nonnegative label; both zero-based and one-based labels accepted; HUD uses actual progression index + 1 |
| `lives` | 3 | Integer 1..10 |
| `pacgum` | 0 | 0 fills all reachable non-spawn/non-power corridors; a positive count samples reachable cells and is clamped to capacity |
| `points_per_pacgum` | 10 | Integer 1..1000 |
| `points_per_super_pacgum` | 50 | Integer 10..3000 |
| `points_per_ghost` | 200 | Integer 15..5000 |
| `seed` | `"42"` | Positive integer or integer string, 1..2147483647 |
| `level_max_time` | 90 | Integer 1..500 seconds; expiration ends the game |
| `window_width`, `window_height` | 2000, 1000 | 320..3840 and 240..2160; actual window is capped to the native display minus a decoration margin |
| `power_duration` | 8 | Finite number 0.1..120 seconds |
| `ghost_respawn_time` | 5 | Finite number 0.1..120 seconds |
| `player_speed`, `ghost_speed` | 5, 4 | Finite number 0.1..30 cells/second |

JSON booleans are not accepted as numeric settings. Malformed JSON, unreadable
files, wrong extensions, invalid UTF-8, and invalid root objects fall back cleanly.
Invalid nested level data falls back to the default level list. No config file or
supplied maze-generator file is modified while parsing or generating.

## Highscore

`HighscoreStore` loads a JSON array of `{ "name": "PLAYER", "score": 123 }`
objects at application start. Valid names contain 1–10 ASCII letters, digits or
spaces and cannot be all spaces. Scores are nonnegative integers (not booleans).
Invalid rows are discarded; a missing file starts an empty table. The ten highest
scores are retained in descending order, with stable ordering for ties.

Both win and loss screens show the final score and allow name entry. An empty
bordered field displays `TYPE YOUR NAME HERE` and the screen explicitly says
`TYPE ON YOUR KEYBOARD TO ENTER YOUR NAME`. With the game window focused, type
directly; no mouse click on the field is needed. Typed characters and a drawn
caret are visible. A prominent `PRESS ENTER TO SAVE SCORE` action confirms entry.
An empty
name submitted with Enter becomes `PLAYER`. Writes use a flushed temporary file
in the same directory and atomic replacement, preserving the previous file on
failure. The outcome screen displays save failures and supports retry without
inserting duplicates. Escape explicitly leaves without saving. The main menu
shows the best score and the Highscores view shows the full top ten. JSON keeps
storage inspectable and avoids additional services or credentials.

## Maze Generation

`Maze.generate` adapts directly to
`MazeGenerator((width, height), perfect=False, seed=seed)` from the supplied wheel.
The assigned package is used as-is. Its global random-state changes are restored
after generation so it does not perturb other application randomness. Wall masks
use North=1, East=2, South=4, West=8. The adapter validates shape, boundaries,
reciprocal walls, and values before gameplay uses the result.

The generator's solid "42" cells may occupy the geometric center. Pac-Man starts
at the nearest accessible central cell; ghosts and power pellets use the four
reachable corners. Dots are placed only in the connected component containing
the player. Generator failures show a recoverable error screen with a return to
menu, rather than replacing the assigned generator with a private implementation.

## Implementation

Positions are floating-point cell-center coordinates; turns and wall checks occur
at reached centers. Rendering derives every pixel position from one integer cell
size, avoiding accumulated rounding drift. Time is monotonic elapsed seconds,
not frame counts. The simulation subdivides updates and checks swept collisions,
so actors cannot pass through each other between frames.

Ghosts chase using shortest corridor-path distances, and choose greater distances
while edible. Power duration, eaten-ghost respawn, and death-grace timers freeze
when paused. Death consumes one life, resets actors/directions to their spawns,
and grants 1.5 seconds of immunity. Pellets, score and the remaining level timer
survive death. Levels preserve score/lives; a new game resets the entire run.
Completion requires all normal and power pellets. Timer expiration is game over.

Graphics use independent MLX ARGB layers: a cached maze and a cleared dynamic
actor/HUD layer. Images honor native stride and format, use transparent clearing,
and are destroyed before the window/context. The wrapper contains exceptions at
the C callback boundary and reports errors only after returning to Python.

## General Software Architecture

```text
pac-man.py / src.__main__
  -> parsing.Config
  -> pac_man.App (screen/lifecycle coordinator)
       -> GameScreen -> GameSession -> Maze -> assigned MazeGenerator
       -> MainMenu / Instructions / Highscores / LevelComplete / EndScreen
       -> HighscoreStore (validated atomic persistence)
       -> Graphics -> MlxWrapper -> supplied MLX library
```

- `src/session.py`: headless `GameSession`, `Actor`, `Ghost`; gameplay and timers.
- `src/maze.py`: validated external-generator adapter and corridor graph queries.
- `src/screens/`: event handling and presentation, using the existing `Screen` API.
- `src/pac_man.py`: new-run, pause, next-level, victory, game-over, and exit routing.
- `src/events.py`: typed, native-independent actions and separate text events.
- `src/graphics.py`, `src/mlx_wrapper/`: drawing, native input, and resource ownership.
- `src/ui.py`, `src/font_map.py`, `src/colors.py`: retained layout and drawing data.
- `src/game.py` and `pygame_graphics.py`: retained legacy/prototype utilities, not
  imported by the active gameplay path; pygame is not the live graphical backend.

## Project Management

See [project_management](project_management/README.md) for actual milestones,
design/risk decisions, regression coverage, native evidence, and release blockers.
No invented historical schedule, team activity, or public-platform deployment is
presented as completed work.

## Resources

- Authoritative assignment: parent `subject_files/en.subject.pdf`, version 1.5.
- Supplied MLX README, Python binding and native source in `mlx-2.2/`.
- Supplied `mazegenerator-2.1.0-py3-none-any.whl` interface, inspected read-only.
- [Python unittest documentation](https://docs.python.org/3/library/unittest.html).
- [mypy command-line checks](https://mypy.readthedocs.io/en/stable/command_line.html).
- [PyInstaller operating modes](https://pyinstaller.org/en/stable/operating-mode.html).

AI assistance was used to audit the subject and existing code, implement the
headless gameplay, persistence and native-resource fixes, write regression tests,
review runtime failures, build packaging scripts, and draft these documents.
Automated tests and actual native launches were run; the owners must still review
and understand all changes and obtain peer review before evaluation. Public upload,
other-machine validation, and actual curriculum logins are owner actions, not
claims made by this implementation.
