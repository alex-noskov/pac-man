# Final beginner-readability cleanup

## Four collected reviews

The four delegated whole-project reviews were collected from their completed
reports and preserved under [reviews](reviews/):

- [reuse.md](reviews/reuse.md): duplicated decisions and competing implementations.
- [quality.md](reviews/quality.md): names, indirection, clever constructs and tests.
- [efficiency.md](reviews/efficiency.md): dead code and unnecessary work.
- [altitude.md](reviews/altitude.md): which architectural boundaries are justified.

They reviewed the whole first-party project at baseline `a9cc671`, including root
scripts, tests, build/configuration files and documentation. The original reports
contain baseline/concurrent test results and old line references. They are review
snapshots, not the final acceptance results. Applied changes were separately
validated against the completed worktree. The assigned generator, vendor source
and supplied wheels were not modified.

## Changes actually applied

| Area | What was complicated before | What changed / why easier | Behavior |
| --- | --- | --- | --- |
| Ghost decisions | Cached whole-maze shortest-path distances and a hidden cache invalidation key | One shared explicit neighbor loop compares horizontal-plus-vertical distance. Normal ghosts choose closer legal cells; edible ghosts choose farther ones. Normal immediate backtracking is avoided if another exit exists; random selection only breaks ties. No personalities or AI framework. | Intentionally changed from shortest-path chase to local chase/flee, as requested. All four share the same rule. |
| Ghost speed | Default and shipped speed 4, plus a second fallback literal in simulation | `ghost_speed` is the only setting; default and sample are 2 cells/second. The player remains 5 by default. | Intentionally slower and fairer; no ghost speed multiplier by level. |
| Config access/state | String-based `getattr` fallbacks duplicated validated defaults; invalid config rebuilt defaults twice; the screen kept an unused copy of config | Read typed Config fields directly, reuse the original defaults instance, remove unused `GameScreen.config`. | Supported validated-config behavior unchanged. |
| Pellet placement | A nested conditional combined sorting, sampling, conversion and clamping | Ordinary all-corridors/sample `if/else`; only sampled mode sorts, preserving seeded sampling order. | Same placement rules and sampled determinism. |
| Prototype implementations | A dead pixel/frame PacMan, a dead pygame Graphics, and an unused pygame dependency competed with live implementations | Delete `src/game.py` and `pygame_graphics.py`, remove pygame and regenerate the lockfile. Git retains history. | Active game unchanged; unsupported historical prototype import APIs intentionally removed. |
| Layout API | Unused circles, hit tests, mutation/copy/bulk getter APIs and their registry distracted from menu rectangles | Keep the rectangle/text classes and only the menu methods used. Preserve layout math. Pass rectangle arguments by keyword; document/rename local left/top/right/bottom insets. | Active menu geometry and fixed font sizes unchanged; unused historical helpers removed. |
| Dead drawing code | Unused bitmap-sprite/debug-cross drawing methods and commented alternatives | Remove `Graphics.draw_image`, `visualise_dot`, old comments and a commented pointer-mask alternative. | Active drawing/native input unchanged. |
| Menu construction/routing | Four duplicate layout blocks, a repeated name list, string-to-enum lookup and hardcoded final index | One ordinary list of `(layout name, label, destination state)` tuples drives a short construction loop, direct routing and bounds. Remove the redundant font alias. | Order, labels, colors, spacing and non-wrapping navigation unchanged. |
| Native fill/menu reset | Two copies of stride-aware rectangle fill and a redundant transparent clear before opaque black filling | Full fill calls the existing rectangle writer. Four menus only perform the opaque fill. Keep dynamic actor clearing and native padding/format/lifetime checks. | Visible pixels/compositing unchanged. |
| Collision/respawn reading | Single-letter math names, a nested zero-motion conditional, and `map(float, ...)` spawn assignments | Descriptive relative-motion/time names, ordinary zero-motion `if/else`, explicit coordinate conversion, short explanations of the 0..1 time clamp, contact radius and update ordering. | Same swept-collision arithmetic, contact order, timers and respawn behavior. |
| Event tests | Factory/enum names synthesized with reflection and strings | Explicit factory/expected-event pairs, direct text factory calls; add menu-order/boundary regression and simple-ghost cases. | Production event behavior unchanged; tests remain explicit. |
| Documentation | Wrong mouse-support claim, stale layout comments, retained-prototype description and intermediate guide | State keyboard-only navigation, correct comments, document the one active backend/model and final ghost rule; finalize `EVALUATION_GUIDE.md` in learning order. | Documentation only. |

No generic menu builder, new scene framework, dependency container, responsive
layout, dispatch DSL, protocol hierarchy, or advanced ghost AI was introduced.

## Reviewed and deliberately retained

- **App/Screen/GameSession/Maze and Graphics/MlxWrapper/ImageLayer boundaries:**
  responsibilities differ; flattening them would expose native details in gameplay.
- **Continuous movement, short simulation steps, repeated collection/contact checks
  and swept collisions:** checks happen at different moments and prevent missed
  pellets, late power activation and tunneling. Only names/explanations changed.
- **Native callback containment, partial initialization cleanup, idempotent stop/quit,
  deferred destruction, stride/endian/opacity handling:** real safety guarantees.
- **Atomic highscore writes, flush/fsync, validation and retry deduplication:** required
  persistence/error guarantees, not removable ceremony.
- **Maze BFS/reachability and generator RNG restoration:** used for safe spawn/item
  placement, not ghost chase. No new maze cache or pathfinding abstraction added.
- **Startup's initial playable session and reset on Play:** eliminating one extra
  generation would change initialization contracts or add a deferred-start flag.
  Keep reset/timestamp behavior rather than introduce another lifecycle mode.
- **Large gameplay render/update methods:** did not split working phases into helper
  layers merely for line counts. Their order remains visible and tested.
- **App's guard for constructor-bypassing orchestration fixtures:** normal apps always
  have a game screen; changing test setup would add churn without changing gameplay.
- **Short screen-level cheat toggle/reset block and explicit EventFactory methods:**
  not moved into extra helpers or generated dynamically.
- **Mouse-event wrapper API, protocol/reference constants and literal font data:**
  retain tested/native contracts and reference data. The menus themselves are
  documented accurately as keyboard-only.
- **Root/module entry-point argument checks and pre/post package support copying:**
  distinct contracts/timing; no removal based only on apparent repetition.
- **Name-entry filtering versus storage validation:** editing sanitizes characters;
  storage rejects invalid completed or on-disk entries. These jobs differ.

## Remaining submission/release actions

The source implementation is locally testable and the native launch is exercised;
that does not replace an owner checking gameplay difficulty over complete normal
runs, target-machine/distribution compatibility, and human peer review. Actual
curriculum logins must replace README placeholders. Public-platform delivery still
requires an account owner to upload the free unlisted/private build and verify the
downloaded release. Original team/timeline evidence must be supplied by the owners
if required; no historical roles, publishing or external acceptance is fabricated.

See the final response for the exact final test/lint/type-check/run results and
commit IDs. No additional changes are scheduled after the requested final report.
