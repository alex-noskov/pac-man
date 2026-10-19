# Plan and Progress

## Goal

Deliver a complete Pac-Man game that satisfies the subject requirements: configurable gameplay, A-Maze-ing integration, four ghosts, scoring and progression, persistent highscores, a graphical UI, cheat mode, robust error handling, packaging, and project-management evidence.

## Milestones

| Milestone | Planned result | Status / evidence |
| --- | --- | --- |
| Project foundation | Python project, MLX rendering, screens, input and configuration loading | Complete |
| Core movement | Player movement through generated corridors and pacgum collection | Complete |
| Maze integration | Use the assigned A-Maze-ing package unchanged with `perfect=False` | Complete; `src/maze.py` |
| Gameplay model | Separate game rules/state from rendering | Complete; `src/session.py` |
| Ghost gameplay | Four autonomous ghosts, chase/flee behavior, collisions and respawn | Complete; session tests |
| Scoring and lives | Configurable points, lives, death, respawn and game over | Complete |
| Level progression | Fixed-seed first level, random later levels, at least 10 levels, timer and victory | Complete |
| UI flow | Main menu, game HUD, pause, highscores, instructions, level-complete, game-over and victory screens | Complete |
| Persistence | Robust top-10 highscore storage | Complete; `src/highscores.py` |
| Configuration robustness | JSON-with-comments support, defaults, validation and unknown-key handling | Complete; `src/parsing.py` |
| Evaluation tools | Cheat mode for fast peer-review testing | Complete |
| Quality assurance | Automated tests, flake8 and mypy checks | Complete; current suite has 109 tests |
| Packaging | Reproducible standalone-build script and in-package instructions | Complete in repository; final packaged build should be rechecked before submission |
| Public-platform release | Upload a working build to an accepted public platform | Repository does not prove this external action; confirm before defense |

## Current verification

The current development state has been checked with:

```bash
make test
make lint-strict
```

Latest reported results:

- 109 automated tests pass.
- `flake8` passes.
- `mypy --strict --ignore-missing-imports` passes for all project source files.

The final submission should repeat these checks after the last repository changes.
