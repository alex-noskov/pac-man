# Project management and acceptance record

## Scope and working rules

Authoritative requirements: Pacman subject version 1.5 in the parent project's
`subject_files/en.subject.pdf`, read without modification. Changes are confined to
the isolated `dev_branch` worktree; master, the assigned maze-generator package,
MLX vendor source, machine configuration and remote repositories are untouched.
This is an actual remediation record, not a reconstructed historical team plan.

## Plan versus progress

| Milestone | Planned acceptance | Actual evidence |
| --- | --- | --- |
| Baseline audit | Read subject and inspect active call paths | Existing app had no ghosts, timer, pause, score persistence, final victory or loss routing; eight baseline tests included one expected failure |
| Orchestration fix | Consistent screen transitions and cleanup | `c053c38`; render transition regression and failing-loop cleanup both pass |
| Headless gameplay | Testable movement, ghosts, scoring, lives and ten levels | `tests/test_session.py`; includes walking all ten real generated levels without level skip, with invincibility/freeze only to isolate collection |
| Configuration/storage | Safe defaults and atomic top-ten persistence | `tests/test_parsing.py`, `tests/test_highscores.py` |
| Native resources/input | Correct stride/opacity, keypress hooks and lifecycle | `tests/test_graphics.py`, `tests/test_events.py` and actual native screenshots |
| Launcher integration | Exercise main-menu through real outcomes | `tests/test_lifecycle.py`; actual `make run` smoke described below |
| Delivery | Required Makefile, README, packaging and release checklist | Root scripts, `PACKAGING.md`, `INSTRUCTIONS.txt`; public platform upload remains an owner action |

## Confirmed bugs and regression coverage

| Confirmed problem | Root cause / resolution | Regression |
| --- | --- | --- |
| `MLX callback failed: AppState.GAME_OVER` | A valid terminal state was absent from the screen map; add all states and actual terminal views | `test_real_game_over_transition_has_screen_and_name_save` |
| Starting after menu idle immediately expires timer | Game clock was initialized during application construction; reset game and monotonic timestamp on menu-to-play transition | `test_menu_start_resets_clock_and_old_run` |
| Supplied levels silently discarded | Existing labels began at zero; validation rejected label zero | `test_supplied_config_preserves_zero_based_level_labels` |
| Last level attempts another maze or loops completion | App transitions did not call session advancement or route its victory result | `test_final_level_routes_to_victory` |
| Window content inaccessible on shorter displays | Configured height exceeded actual native screen | `test_oversized_window_is_fitted_to_the_display` |
| Ghost colors invisible | RGB values lacked opacity in native ARGB format | Native gameplay screenshot and opaque color values |
| Mid-cell position/pellet errors | Logical cells were advanced on departure and pixels accumulated rounded geometry | Continuous cell-space movement, collection at reached centers; fractional-frame and left-movement tests |
| Large pellet count fails sampling | Unbounded sampling request | Capacity clamp and reachable-cell regression |
| Ghost movement/collision absent | No autonomous actors in active gameplay | Chase/flee, swept collision, single-death, edible-ghost scoring and respawn tests |
| No pause, timer or power expiration | No simulation-owned elapsed-time state | Timer, invalid-delta and pause-freezes-every-timer tests |
| Score/level retained on accidental new run | Screen startup incremented the level instead of resetting a run | New-game state and first-maze determinism tests |
| Clear overlays opaque / trails / leaked images | Native surface opacity and lifecycle not respected | Stride/format, compositing, partial initialization, removal/quit tests |
| Documented WASD did not work | Only arrow keys were mapped; vendor helper hooked release | Native keypress mapping and typed separate text/control events |
| Saving failure loses previous scores or repeats submission | Missing storage design | Atomic replacement failure and UI retry-deduplication tests |
| Seed zero breaks fixed first level | Assigned vendor interprets nonpositive seeds as random | Positive seed validator and deterministic generator tests |
| Disabling cheats retains hidden modifiers | C toggled only the enabled flag | Cheat disable clears invincibility/freeze/speed regression |

## Native execution evidence

The reported failure was reproduced by running the real `make run`; it exited
with the same GAME_OVER callback error. After fixing the state routing and clock,
the real launcher remained running, accepted targeted X11 keypresses, rendered
screens, and exited successfully through its Exit menu (process exit code 0).
Only the Pac-Man client window was targeted; no desktop focus or other apps were
manipulated.

A further native launch verified:

1. Main menu and fitting an oversized configured window to the monitor.
2. Starting gameplay without charging menu time; score/lives/level/time HUD.
3. WASD input, cheat enable/invincibility/freeze and pause/resume.
4. Timed edible appearance and four visible ghosts.
5. Ten-level progression using N/Enter, ending on the actual victory screen.
6. Keyboard name entry (`qa123`), saved JSON readback, and visible highscore row.
7. A new unassisted run where autonomous ghosts exhausted the three lives and
   the actual game-over/name-entry screen rendered without a callback failure.

Screenshots in [evidence](evidence/) show these real windows, not mock renders.
The current name-field acceptance captures are indexed in
[evidence/README.md](evidence/README.md): both outcomes now have a bordered input,
keyboard instruction, visible placeholder/caret, and prominent save confirmation.
Real keyboard submissions `LOSSQA` and `WINQA` were verified in native Highscores
and in the saved JSON, followed by clean native Exit.
The screenshots predate changing the sample pellet count from 41 to 0 (all
corridors) except the newer name-field captures; this is why the earlier native
maze evidence shows a sparse custom dot count.
Automated gameplay tests cover both distributions.

## Architecture and choices

- Preserve `App`, `Screen`, `Graphics`, the percentage-based menu layouts, and
  supplied font/colors; extract simulation from the overcoupled gameplay view.
- Use a headless object model so correctness tests do not need a graphical display.
- Adapt the assigned generator as-is, never replace it with a private generator.
- Ghost chase/flee was simplified in the final readability pass to local
  horizontal-plus-vertical distance comparisons of legal neighboring cells.
  Maze graph traversal is retained for reachability, not for ghost AI.
- Use short time steps and swept collision checks to prevent frame-rate tunneling.
- Treat regular and power pellets as separate sets; consume each once and require
  both sets empty for completion.
- End the game on time expiration. Retain level time after death and freeze time
  during pause. Document these choices rather than leave behavior ambiguous.
- Use atomic JSON top-ten storage rather than a remote service, minimizing external
  dependencies and making corrupted/unwritable files recoverable locally.
- Keep native allocation/destruction in one wrapper and never raise into C.

## Risks and mitigation

| Risk | Mitigation / remaining action |
| --- | --- |
| Vendor generator center occupied by 42 pattern | Nearest accessible center; pellets only in reachable component |
| Generator reinstalled during defense | Use public constructor/property only; no package edits |
| Native display/library incompatibility | Clear startup errors; target-machine binary and graphical acceptance still required |
| Permission or corruption in highscore storage | Validation, recoverable errors, same-directory atomic replacement |
| Fast actors / frame stalls | Continuous movement and subdivision; monotonic seconds rather than frames |
| Public-platform access | Owner creates a free unlisted/private listing and uploads verified archive |
| Unknown actual 42 logins | Owners replace README placeholders before submission |
| Curriculum ownership / understanding | Owners review code, explain decisions, and obtain human peer review |
| Unverified historical team roles | Do not invent them; owners supply their original organization/timeline evidence |

## Team organization and release blockers

Original source and commit history are retained. This remediation used separate
workstreams for the headless engine, configuration/persistence, native wrapper,
integration, packaging and independent code review. Those are implementation
workstreams, not assertions about original students' responsibilities.

Before submission, the owners must supply actual curriculum logins and any
required original team planning evidence, validate the distribution on the target
machine, and upload it to a public platform as a free unlisted/private build.
No account creation, credential use, upload or publication is performed here.
