# Acceptance Test Plan

The acceptance plan maps the subject's important behaviors to automated and manual verification.

## Automated verification

Run from the repository root:

```bash
make test
make lint
make lint-strict
```

Expected final result:

- all automated tests pass;
- flake8 reports no violations;
- mypy reports no errors;
- strict mypy also reports no project-code errors (third-party packages are allowed to lack type stubs).

The current test suite contains 109 tests covering application flow, configuration, maze adaptation, gameplay, UI behavior, highscores, native graphics handling, cleanup, and packaging support.

## Functional acceptance matrix

| Requirement | Verification |
| --- | --- |
| Launch command accepts exactly one JSON path | `tests/test_launcher.py`, `tests/test_app_architecture.py` |
| Missing/invalid config values are handled without traceback | `tests/test_parsing.py` |
| JSON comment lines and unknown keys are supported | `tests/test_parsing.py` |
| Assigned A-Maze-ing package is used with deterministic first level | `tests/test_maze.py`, `tests/test_session.py` |
| At least ten levels are playable | `tests/test_session.py`, supplied `config.json` |
| Player moves only through corridors with arrows/WASD | `tests/test_session.py`, `tests/test_graphics.py` |
| Four ghosts move autonomously, chase and flee | `tests/test_session.py`, `tests/test_simple_ghosts.py` |
| Player loses lives and reaches game over | `tests/test_session.py`, `tests/test_lifecycle.py` |
| Pacgums and power pellets score correctly | `tests/test_session.py` |
| Edible ghosts score and respawn | `tests/test_session.py` |
| Level timer, pause and resume work | `tests/test_session.py`, `tests/test_game_screen.py` |
| Score/lives persist between levels | `tests/test_session.py` |
| Final level routes to victory | `tests/test_lifecycle.py` |
| Cheat mode supports evaluation | `tests/test_session.py`, `tests/test_game_screen.py` |
| Persistent top-10 highscores work and survive file errors | `tests/test_highscores.py`, `tests/test_outcomes.py` |
| Main menu, instructions, highscores, pause and outcome screens fit supported windows | `tests/test_fixed_ui.py`, `tests/test_menus.py`, `tests/test_outcomes.py` |
| Native resources are released safely | `tests/test_graphics.py` |
| Packaging inputs/build errors are handled cleanly | `tests/test_packaging.py` |

## Manual final acceptance

Before submission, perform one real graphical run using the final repository state:

1. Start with `make run` and confirm the main menu renders correctly.
2. Start a game and verify player movement with both arrows and WASD.
3. Confirm score, lives, level and remaining time are visible in the HUD.
4. Eat a normal pacgum and a power pellet; confirm scoring and edible ghost behavior.
5. Pause and resume; confirm gameplay/time remains frozen while paused.
6. Enable cheat mode and exercise invincibility, ghost freeze, extra life, speed and level skip.
7. Reach both game-over and victory flows (cheats may be used for evaluation), enter a name and verify the highscore table.
8. Run `make package`, launch the packaged build, and repeat a short smoke test.
9. Confirm the final build is uploaded to the required public platform and launches from that distribution.
