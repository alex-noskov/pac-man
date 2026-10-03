# What to understand for evaluation

## Start with this flow

`pac-man.py` checks the command-line argument, `parse` builds a safe `Config`,
and `App` opens MLX and shows the main menu. Choosing Play starts a fresh game.
Each frame handles input, updates the game, and draws the current screen.

```text
Main menu -> new game -> gameplay
                         | pause -> resume or main menu
                         | level complete -> next level
                         | last level complete -> victory
                         | no lives / time expires -> game over
Victory or game over -> type name -> Enter saves -> main menu
```

## Main files/classes, in learning order

| Order | File/classes | What to explain |
| --- | --- | --- |
| 1 | `pac-man.py` | Exactly one config argument; usage/startup errors are printed without a traceback. |
| 2 | `src/parsing.py`: `Config`, `Level`, `parse` | Commented JSON, unknown keys, field validation and safe defaults. Gameplay reads these typed fields directly. |
| 3 | `src/models/__init__.py`, `src/events.py` | `AppState` names screens; `Directions` names grid moves; typed `Event` objects connect native keys to the app. Printable keys also emit separate name-entry text events. |
| 4 | `src/maze.py`: `Maze` | Use the assigned generator unchanged with `perfect=False`; validate wall bits; list open neighbors; find reachable cells for safe spawn/dot placement. |
| 5 | `src/session.py`: `Actor`, `Ghost`, `GameSession` | Actor position/direction, the shared simple ghost rule, scoring, timers, collisions, lives and level progression. Testable without a window. |
| 6 | `src/pac_man.py`: `App` | Each frame drains events, updates, renders and applies requested screen transitions. New runs reset; new levels retain score/lives. |
| 7 | `src/screens/game_screen.py`: `GameScreen` | Convert elapsed monotonic seconds into simulation updates; render the maze, actors, fixed HUD and pause choices. Other menus keep the same `Screen` interface. |
| 8 | `src/screens/end_screen.py`: `EndScreen` | Display victory/loss, edit a ten-character name, and use Enter to save or Escape to leave without saving. Failed saves can be retried without duplicate entries. |
| 9 | `src/highscores.py`: `HighscoreStore` | Validate and rank the top ten; load at startup; save with a same-directory temporary file and atomic replacement. |
| 10 | `src/graphics.py`, `src/mlx_wrapper/mlx_wrapper.py` | `Graphics` draws text/shapes; `MlxWrapper`/`ImageLayer` own native images/window, key hooks, pixel stride/opacity and cleanup. |

There is only one live movement model and one backend. The unused pixel/frame
PacMan and pygame prototypes were removed; their history is still in Git. The
trimmed `src/ui.py` only supports the menu rectangle/text layout that is actually
used. Its font constants remain fixed: normal/HUD scale 2, title scale 3.

## Explain the gameplay rules in plain terms

- Movement is measured in **cells per second**, not pixels per frame. The player
  queues a direction; a turn is accepted at a cell center only if that corridor
  is open. Rendering converts the grid position into pixels.
- Ghosts inspect only legal neighbors. Distance is horizontal separation plus
  vertical separation. Normal ghosts choose a closer neighbor, avoiding immediate
  backtracking when another exit exists. Edible ghosts choose a farther neighbor
  and may reverse to flee. Randomness only breaks equally good choices.
- `ghost_speed` is the one common speed setting: default **2 cells/second**.
  `player_speed` defaults to **5 cells/second**. There are no personality classes,
  shortest-path chase routes, or level-based speed multipliers for ghosts.
- Normal dots add configured points. Corner power pellets also start the edible
  timer. Touching an edible ghost adds ghost points, hides it, and starts its
  respawn countdown. It returns to its original corner afterward.
- Normal ghost contact costs one life. Surviving death resets actor positions and
  directions and grants brief immunity; it does not reset collected dots/score.
- Pause freezes movement and all gameplay timers. Both ordinary and power pellets
  must be gone to complete a level. Running out of time ends the run.

## Complexity deliberately kept

Small simulation steps and collision checks prevent actors passing through each
other between frames. Native callback guards prevent Python exceptions escaping
into MLX/C. Wall validation and atomic score saves protect correctness. These are
safety mechanisms, not sophisticated ghost AI; explain their purpose before their
low-level details.

`Maze.distances` uses a graph walk for reachability, not ghost chase decisions.
Collection/contact checks occur both before movement and at reached centers:
removing a repeated-looking check could miss a pellet or apply power too late.
The existing `App` partial-object guard supports isolated orchestration tests;
normal construction always creates its game screen. No new frameworks were added.

## Demonstrate rather than memorize

Run `make validate`. During gameplay, C enables evaluation controls: I invincibility,
F freeze, N level completion, L extra life, B player speed, V edible ghosts. Pause
with P/Escape. Show normal play, power expiration, a lost life, a fresh run, victory,
and name entry/highscores. Know the fixed UI sizes in `src/ui.py` and `config.json`.
The supplied generator itself must remain unchanged; it can be reinstalled during
review. Review the code and practice explaining it to a peer in your own words.
