# Beginner-readability review: architectural depth / altitude

## Scope and verdict

Read-only review of first-party code, tests, configuration, launch/build/clean tools, and architecture documentation on `dev_branch`, baseline HEAD `a9cc6711b967b7dc3410a4e32d6dc47471e84b89`. Read `../subject_files/en.subject.pdf` (version 1.5). No production/test changes, vendor changes, or commits. The only review deliverable is this file.

**Verdict: preserve the principal boundaries.** This is not a project that needs a new architecture. The subject explicitly requires OOP, modular/reusable architecture, an unchanged external generator, error recovery, multiple UI states, persistence, and packaging. `App -> Screen -> GameSession -> Maze` is an understandable responsibility chain, not four interchangeable wrappers. `Graphics -> MlxWrapper -> ImageLayer` separates bitmap drawing from native resource ownership. Flattening these would bring native details into beginner-facing gameplay code.

The strongest simplification opportunity is removing the second, implicit configuration-default policy from the simulation. Other findings are smaller and mostly optional. Do not replace explicit classes/branches with registries, generalized dispatch, a scene framework, new protocols, or ghost personalities.

References below use baseline line numbers. A concurrently authored `tests/test_simple_ghosts.py` appeared during inspection; parent work is replacing cached BFS ghost choices with local Manhattan choices and slowing the default ghosts. That intentional behavior change is out of scope here. Do not interpret older graph-distance tests/documentation as a requirement to restore pathfinding.

## Findings

### A1 — Simulation pretends its validated configuration may lack fields

- **Locations:** `src/session.py:207-208,247-248,262-264,317-318`; declarations/defaults in `src/parsing.py:59-66`.
- **Complexity / beginner cost:** `getattr(config, 'player_speed', 5.0)` makes the reader reason about an undocumented second kind of config, runtime string lookup, and fallback values outside `Config`. It also makes a default-speed change require checking both the model and the simulation. The names and defaults already belong to a validated, typed model.
- **Usage/history check:** `GameSession.__init__` accepts `Config`; its production caller is `GameScreen`. Every inspected test constructing a real `GameSession` supplies a real `Config`, not a partial namespace. These accesses arrived in `0877829`; this is not a legacy caller contract found elsewhere in the repository. The screen's injected mock session is a different seam and does not require a partial config here.
- **Smallest fix:** read `self.config.player_speed`, `.ghost_speed`, `.power_duration`, and `.ghost_respawn_time` directly. Keep defaults/validation solely in `Config`; keep any numeric conversion that actually clarifies units. No helper or new model is needed.
- **Confidence:** high. **Risk: SAFE** for the declared contract and observed callers. **Behavior change:** none for validated `Config`; an undocumented duck-typed object missing fields would stop being accepted. Recheck any external callers before expanding that guarantee.

### A2 — Two abandoned implementations remain discoverable as live game code

- **Locations:** `src/game.py:5-115`, `pygame_graphics.py:1-126`, `pyproject.toml:11`; existing explanation at `README.md:201-202`.
- **Complexity / beginner cost:** the project contains a pixel-per-frame `PacMan` as well as the active cell/elapsed-time `Actor`, and two classes called `Graphics`. A beginner opening `game.py` first can learn the wrong movement model or think the backend is interchangeable. Installing pygame reinforces that ambiguity, despite the launcher using MLX only.
- **Usage/history check:** AST inspection found no first-party imports of `src.game` or `pygame_graphics`; packaging explicitly excludes pygame (`package.py:38`). Blame shows original prototype work, not newly required abstraction. The README already labels both legacy/prototype utilities, so this is a discoverability problem, not a hidden active layer.
- **Smallest fix:** add an unmistakable module-level “legacy prototype; not used by the launcher; active gameplay is src/session.py” label to each file. If the owners approve removing historical public utilities, remove the abandoned files and pygame dependency together, regenerate the lockfile, and retain history in Git. Do not build a backend selector just to justify the prototype.
- **Confidence:** high about in-repo non-use; medium about external consumers. **Risk: SAFE** for labels; **CAREFUL** for deletion/dependency changes. **Behavior change:** no active gameplay change; deletion removes importable historical APIs and changes installation contents.

### A3 — Application transitions accommodate constructor-bypassing test objects

- **Locations:** `src/pac_man.py:88-102`, especially `hasattr(self, 'game_screen')` at line 91; `tests/test_app_architecture.py:157-167,282-305`.
- **Complexity / beginner cost:** the lifecycle coordinator's central method has an apparently optional `game_screen`, even though normal initialization creates it before any transition. A beginner must infer whether a real running application can exist without gameplay. A missing field silently skips new-run/next-level/end-score setup.
- **Usage/history check:** blame attributes the guard to `8c41465`. Tests explicitly use `App.__new__`, assign only a screen map and mock graphics, and omit `game_screen`. Therefore the guard has a demonstrated test-support purpose; it is **not** safe dead code to delete in isolation.
- **Smallest fix:** immediately document that this is compatibility for orchestration-only test doubles, not normal application state. If changing tests is later allowed, have those test fixtures provide the fields the real initializer guarantees, then remove the guard. Preserve timeline tests and actual lifecycle integration tests. Do not add an application factory or dependency container solely for this.
- **Confidence:** high. **Risk: SAFE** for explanation; **CAREFUL** for paired fixture/guard changes. **Behavior change:** none for normally initialized apps; partially initialized objects would no longer bypass lifecycle setup. This is low priority, not an acceptance bug.

### A4 — Cheat-mode lifecycle crosses the otherwise useful view/model boundary

- **Locations:** `src/screens/game_screen.py:83-88`; `src/session.py:53-67,302-320`; `tests/test_game_screen.py:70-81`.
- **Complexity / beginner cost:** individual cheat actions are owned by `GameSession.cheat`, but disabling cheat mode resets several simulation flags in the screen. Explaining “what turns cheats off?” requires looking in both the simulation and the UI. This is a responsibility leak, not excessive call depth.
- **Usage/history check:** `8c41465` introduced the screen reset as a real fix, and the test expressly requires invincibility, freeze, and speed to clear. Deleting those assignments would alter observable behavior.
- **Smallest fix:** optional: put the existing toggle/reset block in one plainly named `GameSession.toggle_cheats()` method and call it from the screen. That is one concrete domain operation, not a new abstraction layer. Keep all existing effects, including retained score/lives and current power-state semantics. Add direct headless coverage if proceeding.
- **Confidence:** high about split ownership; medium that an extra method is worth the churn. **Risk: CAREFUL. Behavior change:** none intended; easy to change cheat-reset behavior accidentally. Skip if the owners prefer the already short explicit block.

## Boundaries checked and deliberately not flagged

- **`Graphics` forwarding methods (`src/graphics.py:19-66`):** blame places the façade in the original implementation. Screens call drawing verbs; tests replace this boundary. It also owns real circle/text rendering. Passing lifecycle/layer operations through the façade is coherent; do not force screens to know `mlx_wrapper` internals to save a hop.
- **`GameScreen.new_game` / `next_level` (`src/screens/game_screen.py:39-50`):** not pure forwarding. They reset the UI clock and invalidate the maze image cache; new game also clears pause selection. Bypassing them risks charging menu time or showing an old maze.
- **`EventFactory` (`src/events.py:38-134`):** verbose but explicit, shared by native input and tests, inherited from the original project. Factory methods preserve control/text/mouse payload conventions. Replacing it with dynamic method generation or a generic event-building DSL would be less beginner-readable. The control and text events emitted for the same printable key are deliberate name-entry support.
- **`Screen` / `ExitScreen` (`src/screens/screen.py:6-36`):** the three-method return-state contract is consumed by `App`; render-requested transitions are explicitly tested. Removing `render` return values or the inert exit screen is a contract change, not a safe line-count improvement.
- **Menu `Layout` and cached absolute geometry (`src/ui.py:128-410` and menu screens):** inherited shared coordinate conversion, not a new responsive framework. The fixed font scales coexist with percentage positioning intentionally. Unused circle/mutation utilities are public historical surface, not enough evidence to delete the whole shared helper. Do not extract a generic menu base just because drawing loops resemble each other.
- **Simulation movement/collisions (`src/session.py:119-164,184-300`):** continuous cell motion, center-only turns/collection, subdivision, and swept contact have explicit anti-tunneling tests. These are the lowest-altitude parts of gameplay, but replacing them with frame-count movement would change behavior. Prefer a few explanatory comments about tolerance, substep units, and collision order over more actor/timer classes.
- **Maze adapter (`src/maze.py:19-139`):** validates the assigned wall grid and contains generator failure/RNG effects. BFS remains useful for reachability/spawn/item placement even when ghosts no longer use shortest-path distances. Do not delete `distances` merely because the ghost caller changes; `reachable` delegates to it and a public test asserts it.
- **Parser (`src/parsing.py:127-239`):** reading commented JSON, validation, and per-field fallback correspond to distinct required operations. Keep the nested fallback and existing named helper rather than introducing a validation pipeline or rewriting Pydantic. A duplicate `Config()` construction is a minor local cleanup, not architectural complexity.
- **Highscores / EndScreen:** validation and ranking helpers are shared by load/add; atomic write and retry deduplication meet real failure requirements. Keep storage separate from editing/presentation.
- **Native MLX (`src/mlx_wrapper/mlx_wrapper.py`):** `ImageLayer`, stride/format checks, BaseException containment at C callbacks, deferred destruction, and cleanup of partially allocated resources are safety boundaries. Tests demonstrate why those branches exist. Do not simplify them by narrowing callback catches or freeing the native context while its loop is running.
- **Build/clean tools:** `package.py` command construction and support copying are concrete independently tested operations; the pre-build validation and post-build copying serve different timing needs. `clean.py` protected-directory/symlink checks preserve vendors and evidence. Neither needs a tool framework.

## Verification and limitations

Inspected all tracked first-party Python files, the additional in-progress simple-ghost test file, root configuration/build/launch files, and project documentation. Parsed all 47 tracked first-party Python files with `ast.parse`; no syntax errors. Checked relevant usages and git blame before evaluating forwarding APIs, test accommodations, historical utilities, and shared helpers. Vendor source trees `extract/`, `mlx-2.2/`, and wheels were excluded from modification.

No tests, native launches, dependency installs, bundling, or clean commands were run in this read-only review. Findings are grounded in source/contracts, not a claim of runtime acceptance. The report is under ignored `build/`, so normal `git status` will not list it. Concurrent parent edits must not be attributed to this review.
