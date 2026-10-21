# Acceptance Test Plan

This plan maps the subject's important behaviors to final repository checks and a
real graphical acceptance run.

Automated regression tests were used during development but are not included in
the final submission repository.

## Static verification

Run from the repository root:

```bash
make clean
make lint
make lint-strict
```

Expected result:

- `flake8` reports no violations;
- mandatory `mypy` reports no errors;
- strict `mypy` also reports no project-code errors when third-party packages lack
  type stubs.

## Functional acceptance matrix

| Requirement | Final verification |
| --- | --- |
| Launcher accepts exactly one JSON path | Run valid, missing, and extra-argument cases |
| Missing/invalid config values do not produce a Python traceback | Start with deliberately incomplete/invalid configuration |
| JSON `#` comment lines and unknown keys are accepted | Modify a copy of `config.json` and launch it |
| Assigned A-Maze-ing package is used with `perfect=False` | Review `src/maze.py`; verify generator remains unmodified |
| First level uses a fixed seed and later levels change | Start repeated runs and progress to later levels |
| At least ten levels are configured/playable | Review `config.json`; use cheat mode to traverse levels |
| Player moves only through corridors with arrows/WASD | Manual gameplay |
| Four ghosts move autonomously, chase, and flee when edible | Manual gameplay |
| Player loses a life on hostile ghost contact and respawns | Manual gameplay |
| Pacgums and power pellets score correctly | Manual gameplay |
| Normal pacgums determine level completion | Leave a power pellet uneaten and consume the final normal pacgum |
| Edible ghosts score and return after the respawn delay | Manual gameplay |
| Level timer, pause, and resume work | Manual gameplay |
| Score/lives persist between levels | Complete a level and inspect the next-level HUD |
| Level Complete automatically advances after 3 seconds | Complete a level without pressing a key |
| Enter on Level Complete advances immediately | Complete a level and press Enter |
| Final level routes to Victory | Use cheat mode if needed |
| Cheat mode supports evaluation | Check invincibility, skip, freeze, life, speed, and power |
| Persistent Top 10 highscores work | Save a result, restart, and view Highscores |
| UI remains readable at larger configured windows | Test at `1280x800`, `1920x1080`, or the largest size available on the display |
| Pause menu can resume or return to main menu | Manual gameplay |
| Game Over and Victory accept a valid name and save the final score | Exercise both outcomes |

## Packaging acceptance

Run:

```bash
make package
cd dist/pac-man
./pac-man config.json
```

Verify that the packaged directory contains the executable, `_internal/`,
`config.json`, `INSTRUCTIONS.txt`, and the required support/license files.

Perform a short packaged-build smoke test covering:

1. main menu;
2. starting a game;
3. movement and HUD;
4. pause/resume;
5. cheat mode;
6. level completion and automatic continuation;
7. highscore save/load.

## Release acceptance

Before the defense:

1. Upload the complete verified build to the required public gaming platform.
2. Download or launch the platform-distributed build rather than relying only on
   the local `dist/` copy.
3. Confirm it starts and reaches gameplay.
4. Keep the release available for peer evaluation.
