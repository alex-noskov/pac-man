# Plan and Progress

## Goal

Deliver a complete Pac-Man game that satisfies the subject requirements:
configurable gameplay, A-Maze-ing integration, four ghosts, scoring and
progression, persistent highscores, a graphical UI, cheat mode, robust error
handling, packaging, and project-management evidence.

## Milestones

| Milestone | Planned result | Current status |
| --- | --- | --- |
| Project foundation | Python project, MLX rendering, screens, input and configuration loading | Complete |
| Core movement | Player movement through generated corridors and pacgum collection | Complete |
| Maze integration | Use the assigned A-Maze-ing package unchanged with `perfect=False` | Complete; `src/maze.py` |
| Gameplay model | Separate game rules/state from rendering | Complete; `src/session.py` |
| Ghost gameplay | Four autonomous ghosts, chase/flee behavior, collisions and respawn | Complete |
| Scoring and lives | Configurable points, lives, death, respawn and game over | Complete |
| Level progression | Fixed-seed first level, random later levels, at least 10 levels, timer and victory | Complete |
| UI flow | Main menu, HUD, pause, highscores, instructions, level-complete, game-over and victory screens | Complete |
| Persistence | Robust Top 10 highscore storage | Complete; `src/highscores.py` |
| Configuration robustness | JSON-with-comments support, defaults, validation and unknown-key handling | Complete; `src/parsing.py` |
| Evaluation tools | Cheat mode for fast peer-review testing | Complete |
| UI polish | Responsive text for larger windows and clear level-complete continuation | Complete |
| Quality assurance | Development regression testing, flake8, mypy, and manual acceptance checks | Complete as a development process; final submission uses lint/type checking and manual acceptance |
| Packaging | Reproducible standalone build script and in-package instructions | Complete in repository; final packaged build must be checked after the last change |
| Public-platform release | Upload a working build to an accepted public platform | External action; confirm before defense |

## Progress and verification

Automated regression tests were used during development to validate application
flow, configuration, maze adaptation, gameplay, UI behavior, highscores, native
graphics handling, cleanup, and packaging behavior. Those development tests are
not included in the final submission repository.

For the final repository state, run:

```bash
make clean
make lint
make lint-strict
make package
```

Then launch the packaged build and complete the manual acceptance checklist in
`ACCEPTANCE_TEST_PLAN.md`.

The final remaining external release task is to upload the verified build to the
required public gaming platform and test that uploaded distribution before the
defense.
