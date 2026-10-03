# Beginner-readability review: unnecessary work and dead code

## Scope and evidence

Read-only review of the first-party project at `a9cc671` on `dev_branch`. Line references below describe that snapshot, not subsequent concurrent edits. Reviewed all tracked first-party Python (application, root scripts and tests), configuration/build files, lockfile dependency entries, and documentation. Supplied `extract/`, `mlx-2.2/` and wheels are excluded from cleanup recommendations and were not modified. Screenshot evidence is not executable code and is not proposed for deletion.

The active path is `pac-man.py` -> `src.pac_man.App` -> screens -> `GameSession` / `Maze`, with `Graphics` -> `MlxWrapper` for display. Repository-wide text searches and Python AST name/attribute-use checks were cross-checked against actual imports, decorators, tests and git history. A method without an ordinary call is not automatically dead: Pydantic validators, native callbacks, screen polymorphism and exports must be preserved.

Verification performed with `.venv/bin/python -B`:

- All **104 tests in the tracked test modules passed** (1.178 seconds in this run).
- Initial discovery found **110 tests and 3 failures**, all in the concurrently added, untracked `tests/test_simple_ghosts.py`: local rather than graph chase, anti-reversal, and default speed 2. These were the parent agent's in-progress ghost changes, not failures in the tracked baseline. The parent must run complete discovery again after finishing those changes.
- Instrumented real maze generation with mocked graphics: app/menu construction generates one maze; first Play generates it again (total two).
- Instrumented one real `GameSession` construction: two `Maze.distances` calls occur in level setup.
- Compared buffers using existing `FakeMlx`/`ImageLayer`: clear followed by opaque black fill and opaque black fill alone produced identical bytes for the tested initialized, padded surface.

No production, test, dependency or vendor files were changed by this review. Only this report was written. No native GUI launch or packaging rebuild was performed.

## Findings, ordered by cleanup value

### 1. Two unused implementations obscure which game actually runs

**Files:** `src/game.py:1-115`, `pygame_graphics.py:1-126`, `pyproject.toml:11`, `uv.lock:202,217,333-352`, `README.md:201-202`.

**Evidence/history:** No first-party code or test imports `src.game.PacMan` or `pygame_graphics`. `GameScreen` now owns a `GameSession`, which moves `Actor` objects. `src/game.py` was introduced in `b22b175` for the old pixel-movement screen; `8c41465` replaced the gameplay view with the session-based implementation. Pygame is the earlier backend: `ab37b82` explicitly says “pygame graphics is slow, trying to use mlx.” The README already calls both modules retained prototypes; PyInstaller deliberately excludes pygame.

**Cost:** Two conflicting explanations of movement/rendering for a beginner, plus an installed dependency with no active runtime/test use. The old circle bitmap's square roots/string concatenation have **no current gameplay cost**, so optimizing that method would miss the real issue.

**Concrete fix:** If historical prototype support is not an explicit deliverable, delete the two first-party modules and remove pygame from project dependencies; regenerate `uv.lock` with uv rather than editing generated lock data manually. Update the README's retained-prototype note. Keeping the PyInstaller pygame exclusion is harmless; decide separately whether to remove its packaging-test expectation. Git retains the historical versions, so no new legacy abstraction/directory is necessary.

**Confidence/risk/behavior:** High confidence for no in-repo use. Low risk to the supported launcher; intentionally removes the legacy import API. Confirm owners do not need prototypes before deletion. Validate frozen install, full tests and packaging afterward.

### 2. `Layout` contains an unused circle and editing API

**File:** `src/ui.py:10-54,98-103,134,150-223,231-246,283-330,396-410`.

**Evidence/history:** Screens use rectangle registration, horizontal centering, absolute rectangle conversion and `get_rect_names`. No first-party/test consumer calls `add_circle`, circle conversion/enumeration, `contains`, `replace_rect`, `resize_rect`, `change_text_rect`, `center_rect_y`, `get_rect`, or bulk rectangle conversion/copy methods. Circle classes only refer to each other inside this unused branch. Circle/hit-test additions trace to old gameplay in `b22b175`; the current gameplay view draws grid-space actors directly rather than through `Layout`.

**Cost:** Beginners must understand a generic shape/editing system that the game does not use. Every `Layout` also allocates an empty `_circles` dictionary, although runtime cost is negligible.

**Concrete fix:** Trim only the unreferenced members: `Circle`, `AbsoluteCircle`, `AbsoluteRect.contains`, `_circles`, all circle methods, `replace_rect`, `resize_rect`, `change_text_rect`, `center_rect_y`, `get_rect`, `get_all_rects_absolute`, and `get_all_rects`. Remove `copy` import only after these copy-producing methods disappear. Preserve `Rect`, `AbsoluteRect`, `AbsoluteText`, `Layout.add_rect`, `center_rect_x`, `get_rect_absolute`, `_calculate_text` and `get_rect_names`; do not replace the existing menu layout mechanism.

**Confidence/risk/behavior:** High for repository-only usage. Low runtime risk, but removes unused public helpers and possible external callers. Full fixed-UI/menu tests should remain unchanged. No new layout abstraction is warranted.

### 3. Obsolete bitmap/debug drawing methods and commented alternatives

**Files:** `src/graphics.py:83,102-142`, `src/mlx_wrapper/mlx_masks.py:2`.

**Evidence/history:** `draw_image` and `visualise_dot` have no first-party or test callers. Both originated with the old bitmap player/debugging work in `b22b175`. Current actors use `draw_circle`; text uses the live `draw_text` path. The commented `char_height`, mouse-position method and alternate pointer mask are not live alternatives.

**Cost:** Dead drawing API and unexplained old comments distract from the short active facade. No runtime savings from removing functions that are never called.

**Concrete fix:** Remove those two unused graphics methods and commented-out alternatives. Keep actual text/circle/rectangle drawing and all lifecycle forwarding methods. Do not change the live pointer mask value as part of comment cleanup.

**Confidence/risk/behavior:** High; low supported-game risk, legacy API removal only.

### 4. Four menus clear a surface immediately before completely covering it

**Files:** `src/screens/main_menue_screen.py:62-63`, `highscores_screen.py:45-46`, `instructions_screen.py:61-62`, `level_complete_screen.py:48-49`; implementation `src/mlx_wrapper/mlx_wrapper.py:61-75`.

**Evidence/history:** Each sequence targets the default `main` layer and calls `clear()` followed immediately by `fill(BLACK)`. `BLACK` is opaque (`0xFF000000`); fill writes every visible pixel. Blame shows the main-menu clear predates the later addition of black fill. Existing end/error screens already use opaque fill without a preceding clear.

**Cost:** Every rendered menu frame allocates a zero-byte buffer as large as the mapped layer and writes it, then writes every visible pixel again for black fill. This is real recurring work, unlike unused prototype methods.

**Concrete fix:** Remove only those four redundant menu `clear()` calls, retaining `fill(BLACK)`. The padded-buffer probe gave identical results for the initialized test surface. Native padding does not form visible image columns, but preserve stride-aware fill and keep regression coverage for padded images.

**Confidence/risk/behavior:** High for opaque full-layer replacement; low visual risk. Re-run compositing/fixed-UI tests and native menu transitions. **Do not remove `g.clear('actors')`, general `ImageLayer.clear`, or transparent clearing:** overlays depend on those to avoid trails.

### 5. Duplicate configuration defaults hide the real source of truth

**File:** `src/session.py:207-208,247-248,262-264,317-318`; definitions `src/parsing.py:59-66`.

**Evidence/history:** `GameSession` requires a validated `Config`; all four optional-looking fields are declared on it. Every in-repo actual session construction supplies `Config`. `getattr(config, 'ghost_speed', 4.0)` and the other fallback expressions duplicate the model defaults and suggest those attributes can be absent. These expressions came with `0877829`, alongside the declared configuration fields.

**Cost:** A beginner changing one speed/duration must wonder which number controls behavior. The pending default ghost-speed change makes the stale fallback especially easy to overlook. Lookup speed is not the important concern.

**Concrete fix:** Use `self.config.player_speed`, `self.config.ghost_speed`, `self.config.power_duration` and `self.config.ghost_respawn_time` directly. Retain float conversion where it makes timer/position intent clearer, or remove only truly redundant conversions once types are checked. Configure defaults in `Config` and deliberate shipped overrides in `config.json`; do not add another defaults registry.

**Confidence/risk/behavior:** High for the declared/in-repo API. Low risk; unsupported duck-typed configs missing attributes would now fail instead of silently defaulting. No intended behavior change for validated configs. Parent owns the separate change to ghost speed 2.

### 6. Invalid config handling constructs the same defaults twice

**File:** `src/parsing.py:188,199-200`.

**Evidence/history:** `defaults = Config()` is already computed before validation to print missing-field messages. On `ValidationError`, another identical `Config()` is constructed. Blame shows line 199 is original fallback code, while the new pre-validation default object was added in `0877829`.

**Cost:** One extra Config/default-level construction on invalid input, and a misleading second initialization in a straightforward fallback flow. Startup-only cost, not a frame-performance issue.

**Concrete fix:** Remove the second `defaults = Config()` and reuse the first object for `model_dump()` and final fallback. Preserve both validation passes, field-specific fallback diagnostics, and malformed-input handling.

**Confidence/risk/behavior:** High; very low risk; no intended behavior change.

### 7. Startup creates a level that first Play immediately discards

**Files:** `src/pac_man.py:40,92-94`, `src/screens/game_screen.py:28-30,39-44`, `src/session.py:51,67,80`.

**Evidence/history:** `App` eagerly builds `GameScreen`; its default `GameSession` constructor immediately calls `new_game`, generating the first maze and placing actors/pellets while the menu is visible. Menu-to-Play then calls `new_game` again. Instrumentation observed exactly one generation before Play and two afterward. `8c41465` introduced the menu-start reset for a documented correctness bug: menu idle time was charged against the level timer.

**Cost:** One wasted first-maze generation, validation, graph setup and object/item allocation at normal startup. It also generates a maze when the user only opens instructions/highscores and exits.

**Concrete fix:** A small, explicit deferred-start option for app-owned session construction can postpone initial `new_game()` until Play, while direct `GameSession(config)` remains an immediately playable model for current tests/users. Preserve the screen timestamp reset and the reset-on-every-new-run contract. Add regressions proving no generation in the menu and exactly one on first Play. Do not simply delete `_transition_to`'s reset or reuse an old run blindly.

**Confidence/risk/behavior:** High that work is duplicated; **medium change risk** because initialization/lifecycle assumptions and error timing change. Defer until after the simpler dead-code changes unless parent specifically elects to adjust lifecycle. No new session manager/architecture is justified.

### 8. All-pellet mode sorts a set only to turn it back into a set

**File:** `src/session.py:88-93`.

**Evidence:** `choices` is always sorted. For default `pacgum == 0`, the resulting list is immediately converted back to a set; ordering contributes nothing. For positive counts the sorted list is important for reproducible seeded sampling.

**Cost:** Avoidable sort/list allocation once per generated level. Small bounded grids mean this is not a bottleneck, but the branches can express the rules more plainly.

**Concrete fix:** Keep available pellet cells as a set; assign that set directly for zero-count/all-corridors mode. Only positive-count mode should pass `sorted(available)` into the existing seeded `sample`, still clamping its amount. Use an ordinary `if/else`, not a new helper class or cache.

**Confidence/risk/behavior:** High; low risk if positive-count ordering is preserved. Test both all-corridor placement and fixed-seed sampled placement.

### 9. Mouse events are produced and drained but no screen consumes them

**Files:** `src/mlx_wrapper/mlx_wrapper.py:233-242,309-311`, `src/events.py:15-16,121-129`, `INSTRUCTIONS.txt:11`.

**Evidence:** Repository-wide screen search found no `MOUSE_MOVE` or `MOUSE_DOWN` branch; only event producers and wrapper tests mention them. Native motion/button hooks create events which the app dequeues and screens ignore. Instructions nevertheless say mouse buttons are supported. The historical UI includes hit-testing helpers, but those are no longer called.

**Cost:** Input events, allocations and dispatch work on pointer motion with no game effect; more importantly, a false interaction expectation for users/readers.

**Concrete fix:** Immediately correct the mouse-support sentence in instructions to describe keyboard navigation. Removing mouse hooks/callbacks/events is optional, not an automatic cleanup: existing `test_events` and `test_graphics` explicitly preserve that wrapper API. If owners decide to make the app keyboard-only, remove producer plumbing and deliberately revise those contracts together. Do not implement mouse navigation just to justify old code.

**Confidence/risk/behavior:** High for ignored screen input. Documentation fix is low risk; removing wrapper API is medium risk and intentionally changes the supported event surface. Native close/key callback safety must remain intact.

### 10. Small unused state/constants can be trimmed without redesign

**Files:** `src/screens/game_screen.py:33`; `src/colors.py:3,8,10`; `src/mlx_wrapper/mlx_keycodes.py:6-17`; `src/mlx_wrapper/mlx_constants.py:6,8-9,13,15,24`.

**Evidence:** `GameScreen.config` is assigned but never read; the real session owns configuration. `RED` and `GREEN` have no consumers. `TRANSPARENT` has only the unused pygame consumer. Letter-key constants have no consumers because `_queue_key` visibly uses `ord('w')` etc. Several old X11 event/mask constants likewise have no imports/use in first-party code.

**Cost:** Minor clutter, no meaningful execution cost. Enumerated protocol constants can reasonably be retained as reference data, so these are lower-priority than dead implementations.

**Concrete fix:** Remove unused `GameScreen.config`; optionally remove genuinely unused colors/constants (including `TRANSPARENT` only if pygame is removed). Choose either the existing readable `ord` mapping or named letter constants consistently, rather than retaining both descriptions. Keep `AppState` and `Directions` unchanged: all states are mapped and the direction enum is central to movement/wall checks.

**Confidence/risk/behavior:** High repository-use confidence; low supported-game risk, public constant API removal if trimmed.

## Unnecessary work observed but not recommended for this style pass

- **Repeated spawn/reachability setup:** `GameSession._load_level` gets `center_spawn`; `corner_spawns` computes it again and does BFS; pellet setup does a second BFS. The probe confirmed two distance traversals per initialization. Both have real purposes. Avoid turning clear immutable-maze queries into a cache framework just to save tiny startup work. If measured startup cost warrants it, pass a single already-computed reachable set into an explicit spawn-selection function; this would be a larger API edit, not an immediate safe deletion.
- **Per-event mapping dictionaries:** `GameScreen.handle_event` and `_queue_key` rebuild small mappings. Events are sporadic, and maps local to the handling code are understandable. Hoist only if doing so improves reading; do not add a dispatch framework.
- **Pellet/text rasterization each gameplay frame:** The maze walls are already cached. Dynamic actors/HUD/pellets are redrawn. Further layering/dirty-region/font caching adds state and invalidation rules; no measured native bottleneck was established here, so do not complicate the beginner-facing code.
- **Repeated full menu redraw:** Static screens redraw every loop. Retained cached layouts already avoid geometry recalculation. Apart from redundant clear, render-on-dirty state is an architectural tradeoff, not a proven safe style fix.
- **Pre/post support copying in `package.main`:** Pre-copy checks required inputs before the expensive bundler; post-copy restores files after output replacement. Preserve preflight validation. Separating validation from copying could avoid the first copy, but PyInstaller dominates cost, and removing preflight would regress the documented contract.
- **Ghost BFS:** Baseline `GameSession._choose_ghost_direction` caches distances for the current maze/player cell. Replacing graph distance with Manhattan distance changes decisions through winding corridors, not just implementation style. Parent owns that explicitly requested change, anti-reversal/dead-end logic, tie randomness and speed configuration. Keep `Maze.distances`/`neighbors`: reachability and tests still need graph traversal even after ghost BFS disappears. Update README/project-management statements and graph-specific tests when behavior changes.

## Protective complexity that is not dead code

Preserve these unless a separate change provides concrete equivalent safety and regression proof:

- Native image validation, clipping, `line_length` stride and byte-format handling; native memory is not a simple flat width-times-height Python array.
- Independent layer ownership, transparent actor clearing, black compositing base and native source-over behavior; full opaque menu fill is the narrowly safe exception in finding 4.
- Idempotent quit/destroy/stop, partial initialization cleanup, attempting all cleanup after failure, deferred release until the native loop returns, and containment of even `BaseException` at the C callback boundary. Multiple cleanup calls are intentionally safe, not evidence of dead work.
- Validation/fallback diagnostics in config parsing, maze wall reciprocity/bounds checks, random-state restoration around the supplied generator, and atomic same-directory highscore replacement/retry deduplication.
- Center-aware continuous movement, update subdivision, initial contact handling and swept collision checks. Pre/post collection/collision calls address different timing cases; “called twice” alone is not sufficient proof to remove them.
- `Screen` polymorphic methods, Pydantic validators and native callbacks. AST unused-name output must not be used to delete these implicit entry points.
- Wrapper `remove_layer`, `has_layer` and `get_layer`: not used by current screens, but concrete graphics lifecycle tests exercise them. The small `Graphics` forwarding facade is deliberate separation, not a reason to collapse native implementation into screens.
- Root/module launch checks: both `pac-man.py` and `src.pac_man.main` check arguments, but the latter is separately exercised and called by `python -m src`. Removing one without consolidating entry-point contracts changes error behavior.
- Font-map glyph data and evidence/history documentation. Lowercase glyphs remain used by menu hints; unused punctuation/reference data is not worth pruning speculatively.

## Recommended sequence

1. Confirm prototype retention is not required; remove unused prototype/dependency and genuinely dead drawing/layout members.
2. Apply the narrowly safe local edits: redundant opaque-menu clears, direct Config attributes, duplicate defaults construction, unused `GameScreen.config`, conditional pellet sorting.
3. Correct the false mouse instructions independently of any event-API decision.
4. Treat startup deferral and the parent's ghost policy as explicit behavior/lifecycle changes with dedicated tests, not incidental style cleanup.
5. Re-run full discovery, lint/type checks, and a real native menu/game/outcome/exit smoke test after implementation. This review itself does not claim those future checks passed.
