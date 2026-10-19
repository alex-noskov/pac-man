# Risk Analysis

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Assigned generator changes or is reinstalled during evaluation | Maze integration could fail | Depend only on the assigned package's public interface; keep it unmodified and handle generator errors cleanly |
| Generated geometric center is not walkable | Invalid player spawn / unreachable content | Select the nearest accessible center cell and use its reachable component |
| Corner targets are not directly reachable | Ghost or power-pellet placement could be invalid | Select reachable cells nearest the four geometric corners |
| Invalid or incomplete configuration | Startup failure or unsafe gameplay values | Validate each setting, use safe defaults, ignore unknown keys, and report clean messages |
| Large configured pacgum count | Sampling beyond maze capacity | Clamp requested count to available reachable cells |
| Low frame rate / large frame delta | Actors could skip turns, pellets or collisions | Subdivide simulation time and use swept collision detection |
| Immediate repeated deaths after respawn | Lives could disappear in consecutive frames | Reset positions and use a short respawn grace period |
| Highscore file is missing/corrupt/unwritable | Crash or data loss | Validate loaded rows, recover cleanly, and save with atomic replacement |
| Native MLX callback raises an exception | Crash across the C callback boundary | Capture callback failures and release native resources safely |
| Display smaller than configured window | UI may not fit | Fit requested window dimensions to the actual display |
| Evaluator changes gameplay values | Hidden hard-coded assumptions may appear | Keep speeds, score values, timer, lives, seed and other gameplay settings configuration-driven |
| External public-platform upload is forgotten | Mandatory delivery requirement may be incomplete | Confirm the final uploaded build and launch it from the platform before defense |
| Last-minute changes invalidate evidence | Tests/docs may no longer reflect submitted code | Run the final acceptance checklist after the last commit |
