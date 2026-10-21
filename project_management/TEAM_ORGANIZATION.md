# Team Organization

## Contributors

### vpolikha

Main contributions visible in the project history include:

- initial Python project and application architecture;
- MLX-based rendering/input foundation and UI layout work;
- menu and screen flow;
- early gameplay screen implementation;
- player movement and pacgum collection;
- initial maze generation, level switching, and HUD work.

### anoskov

Main contributions to the current completed implementation include:

- restructuring the application into the current `App`, `GameSession`, maze,
  storage, and `src/ui/` modules;
- completion of player/ghost gameplay, collisions, lives, scoring, timers,
  power mode, respawn, cheats, and multi-level progression;
- robust configuration validation and error handling;
- persistent highscore handling;
- UI completion, responsive text, and gameplay readability refinements;
- regression testing during development and final acceptance review;
- packaging, cleanup, documentation, and subject-compliance work.

## Working approach

Development was organized by subsystem rather than by maintaining duplicate
implementations. The current repository separates responsibilities as follows:

- `src/app.py` — application lifecycle and screen transitions;
- `src/session.py` — gameplay state and rules;
- `src/maze.py` — adapter around the assigned maze generator;
- `src/parsing.py` — configuration parsing and validation;
- `src/highscores.py` — persistent score storage;
- `src/ui/` — rendering, input translation, layouts, and screens;
- `package.py` — standalone packaging.

Important changes and fixes were reviewed against the subject, then checked with
lint/type checking and manual acceptance. Automated regression tests were also
used during development but are not part of the final submitted repository.

For peer evaluation, both contributors should be able to explain the current
architecture and behavior of the submitted code regardless of who originally
implemented a specific module.
