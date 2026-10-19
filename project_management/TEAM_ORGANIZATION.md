# Team Organization

## Contributors

### vpolikha

Main contributions visible in the original project history include:

- initial Python project and application architecture;
- MLX-based rendering/input foundation and UI layout work;
- menu and screen flow;
- early gameplay screen implementation;
- player movement and pacgum collection;
- initial maze generation, level switching, and HUD work.

### anoskov

Main contributions to the current completed implementation include:

- restructuring the application into the current `App`, `GameSession`, maze, storage, and `src/ui/` modules;
- completion of player/ghost gameplay, collisions, lives, scoring, timers, power mode, respawn, cheats, and multi-level progression;
- robust configuration validation and error handling;
- persistent highscore handling;
- UI completion and gameplay readability refinements;
- automated regression and acceptance tests;
- packaging, cleanup, documentation, and final subject-compliance work.

## Working approach

Development was organized by subsystem rather than by maintaining duplicate implementations. The current repository separates responsibilities as follows:

- `src/app.py` — application lifecycle and screen transitions;
- `src/session.py` — gameplay state and rules;
- `src/maze.py` — adapter around the assigned maze generator;
- `src/parsing.py` — configuration parsing/validation;
- `src/highscores.py` — persistent score storage;
- `src/ui/` — rendering, input translation, layouts, and screens;
- `tests/` — regression and acceptance-oriented automated tests;
- `package.py` — standalone packaging.

For peer evaluation, both contributors should be able to explain the current architecture and the behavior of the submitted code, regardless of who originally wrote a specific module.
