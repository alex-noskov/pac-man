# Beginner-readability review

## Scope and evidence

Read-only review of the first-party project at baseline `a9cc671` on `dev_branch`: every tracked Python file in `src/`, root launcher, packaging/cleanup scripts, retained Pygame prototype, all tracked tests, and configuration/build/documentation files. Also read the concurrently added `tests/test_simple_ghosts.py`. Read `../subject_files/en.subject.pdf` (version 1.5). Excluded unchanged `extract/`, `mlx-2.2/`, supplied wheels, environments and generated output. Font data was inspected as data, not treated as an oversized method.

Checked usages and targeted git blame before proposing changes. Existing menus/layout were mostly introduced in the original student commits; session and native safety code mainly in `0877829d`, `81c58e65`, and `8c41465d`. Preserve those architectural boundaries and resource guarantees. Findings below are suggestions, not applied patches. The parent is already changing ghost decisions/speed; this report deliberately does not propose a competing ghost algorithm or changes to its pending tests.

Risk: **SAFE** = localized, readily behavior-preserving; **CAREFUL** = order/contracts require regression tests; **RISKY** = likely to change gameplay/native behavior. Confidence describes the finding, not a guarantee about an unimplemented fix.

## Findings

### Q1 — Validated settings are accessed as though they might not exist

- **Location:** `src/session.py:207-208`, `247-248`, `262-264`, `317-318` (baseline line numbers).
- **Problem / beginner cost:** `getattr(self.config, 'power_duration', 8.0)` and similar accesses add a second source of defaults and hide field names inside strings. A reader has to decide whether the session supports older/ad-hoc config objects. Its constructor explicitly accepts `Config`, and that class already declares, defaults and validates all these fields. Tests construct real `Config` objects; their mocked session is injected at the screen boundary, not used as a replacement config.
- **Plain Python fix:** Read `self.config.power_duration`, `self.config.ghost_respawn_time`, `self.config.player_speed` and `self.config.ghost_speed` directly. Retain conversions only where the receiving operation needs them. Let `Config` remain the single source of defaults. Coordinate with the parent's pending speed change rather than retaining the old fallback value.
- **Confidence:** high. **Risk:** SAFE for the declared `Config` API. **Behavior change:** none for validated configs; missing attributes on an undocumented duck-typed config would no longer silently fall back.

### Q2 — Test construction leaks into production transition logic

- **Location:** `src/pac_man.py:91`; `tests/test_app_architecture.py:157-167`.
- **Problem / beginner cost:** `hasattr(self, 'game_screen')` guards the game's main lifecycle transitions even though normal `_initialize_screens()` always assigns `game_screen`. The architecture tests create an incomplete `App` with `App.__new__` and supply only state/screens/graphics. This makes a learner infer that a real App may validly lack its game session and silently skip new-game/level/outcome setup.
- **Plain Python fix:** Give the test fixture an explicit minimal game-screen double (and a session with a known state/score); then remove the missing-attribute guard from the real transition path. Keep orchestration tests isolated using ordinary doubles, not a production compatibility branch. Keep the `EndScreen` check until screen-map typing is addressed deliberately.
- **Confidence:** high (usage and blame confirm lifecycle introduction in `8c41465d`). **Risk:** CAREFUL: update transition tests alongside the fixture; new-game transitions intentionally read the session state after initialization. **Behavior change:** none for normally constructed apps; malformed partial instances stop receiving silent special treatment.

### Q3 — One render method contains nearly the entire gameplay presentation

- **Location:** `src/screens/game_screen.py:116-199`.
- **Problem / beginner cost:** `render()` mixes the error screen, geometry, cached wall generation, pellets, sprites, HUD/cheat status and pause overlay. Nested wall tuples plus `g`, `s`, `cell`, `w`, and `h` make it harder to find the small section to change for evaluation. Unlike the font table, this is executable multi-responsibility code.
- **Plain Python fix:** Keep `render()` as the visibly ordered coordinator. Extract only substantial blocks into private methods such as `_draw_maze(maze, cell_size, left, top)`, `_draw_hud()` and `_draw_pause_menu(width, height)`. Use `cell_size` rather than `cell` where it denotes pixels per cell. Keep direct arithmetic and the existing fixed constants; no renderer strategy, new layout object, responsive UI or generic widget framework.
- **Confidence:** high. **Risk:** CAREFUL: retain cache identity checks, layer creation/order, one clear of actors, and refresh after all drawing. **Behavior change:** none intended; fixed-UI and graphics-boundary tests must remain unchanged and pass.

### Q4 — Collision mathematics is correct-looking but difficult to explain from the names

- **Location:** `src/session.py:184-195`.
- **Problem / beginner cost:** `_swept_touch()` compresses relative motion and closest approach into `rx`, `ry`, `vx`, `vy`, `length`, a nested conditional/clamp, and an unexplained `0.35`. `length` is actually squared relative travel, not a length. A beginner cannot easily justify why the projection or threshold prevents swapping/tunneling.
- **Plain Python fix:** Preserve the exact calculation. Name the squared magnitude `relative_distance_squared`, use `closest_time` for `t`, and expand the zero-relative-motion case into an ordinary `if/else`. Add a short comment that time is normalized to this simulation step and that `0.35` is the contact radius in cell units (optionally a named constant). Do not substitute endpoint-only collision checks or remove substeps.
- **Confidence:** high. **Risk:** SAFE if operations/clamping remain identical. **Behavior change:** none intended. Verify `test_midstep_collision_cannot_tunnel_or_swap` and powered-contact tests.

### Q5 — Simulation phase order is implicit inside an overlarge update loop

- **Location:** `src/session.py:252-300`.
- **Problem / beginner cost:** The update method validates input, selects time slices, collects before movement, checks existing contact, moves actors/respawn timers, collects again, checks swept contact, then expires power/grace/level timers. Some repeated-looking operations are deliberate. A learner trying to shorten the function could remove a collect/collision call or expire power too early and change scoring/death behavior.
- **Plain Python fix:** First make these ordered phases explicit with short intent comments, and name `step` as `step_seconds`. If extraction is still helpful, move just the ghost movement/respawn block into `_move_ghosts(step_seconds, ghost_speed)`; keep collision/collection/timer ordering together and visible. Retain early exits on a death/completion and the existing small-step limits.
- **Confidence:** high. **Risk:** CAREFUL. **Behavior change:** none intended; existing fractional-frame, collision-at-start, power expiration, respawn and timeout tests are necessary acceptance checks. This is not a recommendation to simplify the simulation algorithm.

### Q6 — Layout inset names and positional forwarding conceal units and sides

- **Location:** `src/ui.py:109-125`, `136-148`, `360-369`; callers in `src/screens/main_menu_screen.py:108-124`.
- **Problem / beginner cost:** `x_offsetp_rev` and `y_offsetp_rev` require the reader to reverse-engineer that they mean right and bottom text insets, measured as percentages of the rectangle rather than window. `add_rect()` forwards a long group of similarly typed positional arguments to `Rect`, so a swapped side is hard to notice. The brief docstrings do not state the mapping.
- **Plain Python fix:** Preserve the existing public keywords; document left/top/right/bottom and rectangle-relative units in the two entry-point docstrings. Forward to `Rect` using explicit keywords. Use descriptive local names (`right_inset`, `bottom_inset`) for converted pixel values. Do not rename every layout API or replace the percentage system with a new framework.
- **Confidence:** high (original inset introduction `ab37b826`; active main-menu usages verified). **Risk:** SAFE. **Behavior change:** none, including the existing rounding and fixed font sizes.

### Q7 — Event tests reconstruct the API with reflection instead of showing it

- **Location:** `tests/test_events.py:8-26`.
- **Problem / beginner cost:** The control test synthesizes factory and enum member names using `getattr`, string concatenation and `upper()`, then guards an attribute it just asserted exists. A learner must understand the naming convention and runtime reflection to see what event is expected. The text test similarly discovers a method that is already imported on a known class.
- **Plain Python fix:** Use an explicit list of `(EventFactory.key_left, EventType.KEY_LEFT)` pairs and loop over it with `subTest`; call `EventFactory.text('Alex 42')` directly. Keep the ordinary table-driven loop, but eliminate name synthesis and dead-looking optional branches. No dynamic test generator or helper abstraction is needed.
- **Confidence:** high. **Risk:** SAFE. **Behavior change:** no production change; a missing factory fails directly instead of through a preliminary reflection assertion. Keep all current event cases.

### Q8 — Menu routing relies on a hidden equality between widget names and enum names

- **Location:** `src/screens/main_menu_screen.py:47-52`, `108-130`.
- **Problem / beginner cost:** Activation uses `AppState[self._buttons[self._selected]]`. Layout identifiers therefore double as enum member names, while the bounds check separately hardcodes `3`. Changing/adding a beginner-level menu item requires knowing three unstated connections (layout name, state name, last index), and an innocent layout rename can produce a runtime lookup error.
- **Plain Python fix:** Keep an explicit small list of button-name/`AppState` pairs and obtain the target state from the pair rather than enum lookup by string. Derive the last valid index from the list length. Retain the same order, labels, colors and non-wrapping navigation. Do not add a generic action/command system.
- **Confidence:** high. **Risk:** CAREFUL: menu layout caching and selection/color updates must use the same list. **Behavior change:** none for the four existing items; future identifiers no longer have to equal enum names.

### Q9 — Retained prototype modules still look like alternate live implementations

- **Location:** `src/game.py:1-5`, `pygame_graphics.py:1-24`; `README.md:201-202`.
- **Problem / beginner cost:** The README correctly identifies the files as legacy/prototype code, but opening them directly presents another `PacMan` and another `Graphics` with ordinary active-sounding descriptions. Whole-project symbol/usages inspection found no active gameplay imports of them. A beginner searching for movement or drawing can edit these instead of `GameSession` or `src.graphics.Graphics`. The prototype also uses root-relative package imports that are not a standalone launch path.
- **Plain Python fix:** Add concise module docstrings identifying each as retained, non-live prototype code and pointing to the current implementation. Keep the files and API intact unless the owners explicitly approve removal. Do not make the prototype a fallback backend or migrate the live application to it.
- **Confidence:** high (prototype source traces to original commits; live launcher uses only MLX). **Risk:** SAFE for documentation. **Behavior change:** none; deletion/repackaging would require separate approval.

## Documentation inconsistency to address alongside quality work

`INSTRUCTIONS.txt:11` says menu mouse buttons are supported. Native mouse events are queued (`src/mlx_wrapper/mlx_wrapper.py:233-242`), but `MainMenuScreen.handle_event()` handles keyboard controls and close only. This sends a beginner down the wrong implementation path and misleads packaged users. Correct the sentence to the existing keyboard behavior rather than implement new mouse interaction. **Confidence: high; risk: SAFE; behavior change: none (documentation only).** Also remove/update the stale percentage-position comments in `src/screens/highscores_screen.py:79`, `90-92` if editing that file: they describe different coordinates from the actual values.

## Keep as-is / do not over-simplify

- `Screen` plus `App` state mapping, headless `GameSession`, `Maze` adapter and `Graphics`/MLX ownership are understandable boundaries, not unnecessary abstraction layers.
- Keep explicit event factory methods. They are repetitive but simple; Q7 is about the tests, not replacing factories with metaprogramming.
- Keep atomic highscore replacement, flush/fsync, temporary cleanup, guarded native callbacks, partial-construction cleanup and ordered native destruction. Complexity here protects concrete resource/error guarantees.
- Keep the generator unchanged and its random-state restoration. BFS in the maze adapter still serves reachability; removing the parent's old ghost BFS is not a reason to remove maze connectivity checks.
- `FONT_MAP` is literal 5x8 bitmap data; its length is not a quality defect. Do not compress it into encoded strings or runtime generation.
- Root `clean.py` and `package.py` already have small, purposeful functions. Repeated fixed-screen drawing is not sufficient justification for another shared screen framework.
- Pydantic validators/default recovery reflect stated config requirements. Do not replace validation with untyped hand-written coercion purely to reduce lines.

## Verification and limits

- `.venv/bin/python -m unittest discover -s tests`: **110 tests, 3 failures**, during the parent's in-progress ghost change. All failures were in the newly added `test_simple_ghosts`: local (not graph) chase, no immediate reversal, and default/shipped speed two. The baseline implementation still used the old behavior at that moment. These are concurrent RED-stage tests, not newly attributed quality regressions.
- Running the tracked test modules separately: **104 tests, all passed**.
- `.venv/bin/flake8 .`: stopped at `tests/test_simple_ghosts.py:38:43` (`E128`) in the concurrent new test; therefore a full clean lint result is not claimed.
- `.venv/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`: **success, no issues in 48 source files**.
- These checks are snapshots of a shared worktree. Re-run them after the parent completes changes. No native GUI run or packaging rebuild was performed for this read-only review.
- Only this report was written by this reviewer. No source/test/config files edited and no commit made.
