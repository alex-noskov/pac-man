# Whole-project readability review: reuse and duplication

## Scope and verification

Read all first-party `src/**/*.py`, root `clean.py`, `package.py`, `pac-man.py`, `pygame_graphics.py`, all tests, `pyproject.toml`, `setup.cfg`, and Makefile. Reviewed the whole implementation, not only the last commit. Vendor `extract/`, `mlx-2.2/`, and wheel contents were not changed. Source snapshot: HEAD `a9cc671` at review start. Only this report is written.

Baseline verification: `.venv/bin/python -B -m unittest discover -s tests` passed **104 tests**; `.venv/bin/flake8 .` passed; Makefile-equivalent mypy flags passed (**47 source files**), with cache redirected into agent scratch. These are baseline results, not verification of proposed edits. No native UI run or packaging build was performed.

Priority is reducing competing mental models and duplicated decisions, not minimizing lines. SAFE means equivalent for supported inputs; CAREFUL means compatibility or exact rendering contracts need checking; RISKY means a tempting deduplication changes behavior. Parent's planned local-Manhattan ghost movement and speed reduction are separate behavioral work; no alternative AI is proposed here.

## Concrete SAFE simplifications

### 1. Use Config as the one source of gameplay defaults

**Locations:** `src/session.py` `_collisions` around 207–208, `_collect` 247–248, `update` 262–264, `cheat` 317–318; definitions in `src/parsing.py` 55–66.

**Complexity:** The typed session accepts `Config`, but repeatedly calls `getattr(config, 'field', literal_default)`. A beginner has to decide whether an incomplete configuration is supported and which fallback wins. Player speed, ghost speed, power duration and respawn duration already have validated fields and defaults. Power-duration fallback is repeated in two actions.

**Simplification:** Read `self.config.player_speed`, `.ghost_speed`, `.power_duration`, and `.ghost_respawn_time` directly, retaining numeric conversions where useful. No helper, new model, or new constant is needed. This also avoids keeping a stale ghost-speed fallback when the parent changes the default.

**Behavior:** None for the declared Config API. Duck-typed incomplete objects would cease to be accepted; those are not the session's declared interface. Existing screen tests inject a mock session rather than a mock configuration. Run parsing/session/game-screen tests, especially custom float settings.

### 2. Define main-menu button data once, in a short local loop

**Location:** `src/screens/main_menue_screen.py` `_gen_layout` 108–130; navigation 41–50.

**Complexity:** Four nearly identical `add_rect`/`center_rect_x` blocks repeat identical geometry, while `_buttons` repeats the same names elsewhere. The navigation upper bound independently assumes four buttons.

**Simplification:** Use a local sequence of `(name, label)` pairs and an ordinary `for index, (name, label) in enumerate(...)` loop. Keep `yp=20 + 15 * index`, width 25, height 10, and both horizontal insets 5. Populate `_buttons` in that same loop, and replace the upper bound `3` with `len(self._buttons) - 1`. Keep the separate control-hint rectangle; it is not a button. Do not introduce a menu builder or button class.

**Behavior:** None; preserve insertion order, first selection, boundary-clamped navigation (not wrapping), labels, colors, and fixed scales. A local loop teaches repetition more clearly than parallel duplicated lists. Test fixed UI, menu rendering, and lifecycle; add an explicit first/last selection regression before changing navigation.

**History:** `git blame` shows the repeated construction originated in `9b118a28`/`b0d9d5bc`; the fixed scale was changed in `a9cc671`. Preserve the latter.

### 3. Reuse the existing defaults instance on validation failure

**Location:** `src/parsing.py` `validate_with_field_defaults` 188 and 199.

**Complexity:** A Config is constructed to report missing fields and then reconstructed in the error branch, making the reader wonder whether the first one changed.

**Simplification:** Delete only the second `defaults = Config()` and call `defaults.model_dump()` on the first instance. Keep the independent-field replacement and second validation attempt intact.

**Behavior:** None with current validators; missing/invalid fields and final fallback retain the same values and diagnostics. Test malformed files and independently invalid settings. `git blame` identifies the original error-branch construction in `47a97b4` and the added early construction in `0877829d`; neither source path mutates that instance.

### 4. Implement a full-surface fill through the existing rectangle writer

**Location:** `src/mlx_wrapper/mlx_wrapper.py`, `ImageLayer.fill` 66–75 and `put_rectangle` 86–99.

**Complexity:** Both independently convert packed ARGB into native-format bytes and write repeated rows honoring the stride. That is one drawing operation maintained twice.

**Simplification:** Have `fill(color)` call `self.put_rectangle(0, 0, self.width, self.height, color)`. Keep the explanation that MLX's format controls byte order near the shared conversion. Do not change `clear`: it deliberately clears the entire buffer, including padding, unlike a visible-pixel fill.

**Behavior:** None for valid allocated surfaces. Both paths require a live image, write only visible row bytes, and leave padding untouched. Keep the clipping implementation and contiguous row writes, not per-pixel drawing. Existing `test_fill_respects_stride_and_format`, clipping, transparency, and lifecycle tests should pass unchanged. Both row-writing implementations were established in `81c58e65`.

### 5. Do not clear a layer immediately before an opaque full fill

**Locations:** render methods in main menu 62–63, instructions 61–62, highscores 45–46, level-complete 48–49.

**Complexity:** Two consecutive reset operations imply both transparency and black filling are required for ordinary opaque screens.

**Simplification:** Retain the BLACK fill and remove the immediately preceding `clear()` for these main-layer screens. Retain clearing of the dynamic `actors` layer and any real transparent layers.

**Behavior:** None for composited visible pixels. Row padding will not be zeroed every frame, but is not displayed. Fixed UI and compositing tests cover the relevant distinction. If a future backend assigns additional clear-only state, reconsider; that is not the current implementation.

## CAREFUL opportunities: no new abstractions

### 6. Retire the competing prototype implementations, rather than merge them

**Locations:** all of `src/game.py` (pixel/frame PacMan), `pygame_graphics.py` (second Graphics/Image implementation), `pyproject.toml` pygame dependency.

**Complexity:** There are two movement models with different units and two graphics models with different resource/layer contracts. Sharing their algorithms would create adapters and obscure the active path.

**Evidence:** Whole tracked-tree symbol search finds no active imports or tests using `PacMan`, `src.game`, or `pygame_graphics`. README 201–202 explicitly labels these as retained legacy/prototype utilities. Blame shows substantive implementations originated in `b22b1752` and `3a8a0f7b`; later work largely added documentation. Packaging explicitly excludes pygame.

**Simplification:** If retention is no longer required, delete those two first-party modules, remove the unused pygame dependency, regenerate the lockfile with the normal dependency tool, and update the README. Do not touch supplied vendors or wheels. Do not fold their behavior into GameSession/Graphics.

**Behavior/status:** Active game should be unchanged, but removal deliberately breaks prototype import APIs and the README's retention promise. Therefore CAREFUL, not an unconditional safe deletion. Confirm scope with the parent/user first and rerun tests, flake8, mypy, launcher, and packaging verification.

### 7. Trim unused UI/graphics surface before extracting shared machinery

**Locations:** `src/ui.py` circle classes/registry and methods (`add_circle`, replacement/resizing, circle getters/conversion); unused rectangle mutators/bulk accessors; `src/graphics.py` `draw_image` and `visualise_dot`.

**Evidence:** Tracked first-party/test symbol search found only definitions and internal calls for these methods, no runtime/test consumers. Circle classes and registry came from `b22b1752`; graphics bitmap/debug routines likewise. Active GameScreen uses Graphics.draw_circle directly, not Layout circle conversion. Existing menus do use `Layout.add_rect`, `center_rect_x`, `get_rect_absolute`, and instructions use `get_rect_names`.

**Simplification:** Remove the unused circle-layout subsystem as a unit if compatibility allows; separately prune unused convenience methods and debug/bitmap functions. Preserve the rectangle/text types actually used. Do not consolidate the two unused contains methods into a geometry hierarchy, or extract an image-rendering framework to share unused bitmap code.

**Behavior/status:** No known active behavior change, but externally callable utility APIs disappear; CAREFUL because README describes retained layout utilities. Keep `get_rect` until its usage is individually confirmed, and verify whole-tree usages again immediately before any deletion. This review does not assert outside-repository consumers are absent.

## RISKY deduplications to avoid

- **Repeated `_collect`/collision checks in session movement and update:** they establish different moments (frame-start contact, crossed cell centers, end-of-step contact). Removing a call because its name repeats can change power activation, final-dot completion, life loss, and tunneling. Keep the shared `_move` implementation for player/ghost movement, and retain the contact-order tests.
- **Root launcher versus `src.pac_man.main` argument handling:** they look duplicated but have different contracts: root reports usage on stderr and exits 2 before importing native graphics; internal main prints to stdout and returns. Tests assert each separately. Unifying requires a deliberate entry-point/API change, not a safe cleanup.
- **Packaging's two support-file copies:** the first validates required inputs before an expensive build, and the second restores support files after PyInstaller's clean/noconfirm build. Delete neither merely because the calls repeat. Separate validation could be clearer but would add a helper outside this review's requested approach.
- **Global CLOSE plus screen CLOSE branches:** screen handlers are independently callable and still have useful local contracts. Removing them may preserve App behavior but change those contracts. Two simple lines per screen are cheaper than another event framework.
- **Name filtering versus highscore validation:** editing filters incoming characters and limits length; storage rejects an invalid completed entry and invalid disk rows. They intentionally perform different jobs. Do not replace both with one regex/helper that conflates sanitizing with validation.

## Keep the small, intentional duplication

Do not add a generic cached-screen base class, a drawing dispatch framework, or reflective reset helpers. The repeated screen text calls are straightforward and carry different panel colors and placement rules. In particular, EndScreen `_line` takes a vertical center whereas GameScreen `_text` takes a top y coordinate and clamps x; merging them naively moves text. The short STOP assignments and timer clamps in GameSession are easier to understand explicitly than a field-name loop using setattr.

The strongest immediate changes are the direct Config reads and local menu-construction loop. They remove duplicated decisions without creating another concept. Utility deletion offers the largest competing-mental-model reduction but must respect intentional retention/compatibility. No source changes were made by this review.
