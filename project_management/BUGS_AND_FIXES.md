# Bugs and Fixes

This file records representative defects that influenced the current design and the regression tests that protect against their return.

| Problem | Resolution / regression evidence |
| --- | --- |
| A terminal `GAME_OVER` transition could reach a state without a valid screen | Complete screen/state routing and lifecycle tests cover real game-over and victory transitions |
| Menu idle time could leak into a newly started game's timer | Reset the session and frame clock when starting a new run |
| Valid zero-based level labels could be rejected | Configuration validation accepts the supplied level numbering |
| Final-level completion could attempt to load another level instead of showing victory | Session/app progression explicitly routes the final completion to `VICTORY` |
| Actors could collect or collide incorrectly between cell centers | Continuous movement, center-based collection and swept collision checks |
| Fast actors could pass through each other between frames | Collision checks use movement paths, not only end positions |
| Pellet requests larger than the reachable maze capacity could fail | Clamp the requested number to available cells |
| Power expiration could occur in the middle of a large simulation step | Simulation steps stop at the exact remaining power duration when necessary |
| Ghosts could immediately remove several lives after a respawn | Respawn resets positions and applies a short grace timer |
| Pausing could still advance timers or movement | Session updates do nothing while paused and resume resets the external frame clock |
| Turning cheat mode off could leave hidden advantages active | Disabling cheats clears invincibility, ghost freeze and speed modifiers |
| Highscore save failure could corrupt the existing score file | Save to a temporary file and atomically replace the old file only after a successful write |
| Transparent/native graphics layers could trail or leak resources | Graphics tests cover clearing, compositing, stride handling and resource destruction |
| Only some documented movement keys were handled | Input mapping supports arrows and WASD as required |
| Oversized windows could place content outside the physical display | Graphics startup clamps the requested window to the available screen |

Regression tests are kept in `tests/` and are intended to be run before every final build.
