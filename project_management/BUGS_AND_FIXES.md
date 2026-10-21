# Bugs and Fixes

This file records representative defects that influenced the current design and
their resolutions.

| Problem | Resolution / verification |
| --- | --- |
| A terminal `GAME_OVER` transition could reach a state without a valid screen | Completed screen/state routing for game-over and victory paths |
| Menu idle time could leak into a newly started game's timer | Reset the session and frame clock when starting a new run |
| Valid zero-based level labels could be rejected | Configuration validation accepts valid supplied level numbering |
| Final-level completion could attempt to load another level instead of showing victory | Final completion explicitly routes to `VICTORY` |
| Actors could collect or collide incorrectly between cell centers | Use continuous movement, center-based collection, and swept collision checks |
| Fast actors could pass through each other between frames | Collision checks consider movement paths, not only final positions |
| Pellet requests larger than reachable maze capacity could fail | Clamp the requested count to available reachable cells |
| Power expiration could occur in the middle of a large simulation step | Stop simulation substeps at the exact power-expiration boundary |
| Ghosts could immediately remove several lives after respawn | Reset positions and apply a short respawn grace timer |
| Pausing could still advance timers or movement | Session updates stop while paused and resume resets the external frame clock |
| Turning cheat mode off could leave hidden advantages active | Disabling cheats clears invincibility, ghost freeze, and speed modifiers |
| Highscore save failure could corrupt the existing score file | Save to a temporary file and atomically replace the old file only after success |
| Transparent/native graphics layers could trail or leak resources | Explicit layer clearing, compositing rules, and resource cleanup |
| Only some documented movement keys were handled | Input mapping supports arrows and WASD |
| Oversized windows could place content outside the physical display | Clamp requested window dimensions to the available display |
| Text and boxes scaled inconsistently between screens | Use percentage-based boxes with relative padding and box-fitted bitmap text |
| Level-complete flow gave little continuation feedback | Show a countdown, allow Enter immediately, and auto-start the next level after 3 seconds |
| Power pellets incorrectly blocked level completion | Level completion now depends only on normal pacgums, matching the subject wording |

Automated regression tests were used during development to protect these fixes.
They are not included in the final submission repository, so the final submitted
state is verified with lint/type checking and the manual acceptance plan.
