# Native MLX screenshot evidence

These are captures of the actual Pac-Man MLX client window, not rendered mockups.
The source application was launched with `make run` and the supplied `config.json`.
Targeted X11 keypresses exercised the native event hooks without moving desktop
focus or interacting with other applications.

## Current name-entry UI (use these for acceptance)

The latest fixed **1024x640** window captures are:

- `fixed-main-menu.png`, `fixed-instructions.png`, `fixed-highscores.png`:
  readable fixed-size menu text and visible navigation hints.
- `fixed-gameplay.png`, `fixed-largest-maze.png`: HUD and complete first/final
  mazes in the available space, without clipping.
- `fixed-pause.png`: readable pause choices with the HUD still visible.
- `fixed-game-over-empty.png`, `fixed-game-over-name.png`: fully visible loss
  prompt/input/save action, including visible `LAPTOP` keyboard input.
- `fixed-victory-name.png`: fully visible victory input with `LAPTOP` typed.
- `fixed-level-complete.png`: fixed-size completion title.

Normal and HUD glyphs use fixed scale 2; titles use fixed scale 3. These captures
supersede the larger-window screenshots below for laptop-size acceptance.

| Screenshot | What it demonstrates |
| --- | --- |
| [game-over-name-empty.png](game-over-name-empty.png) | Game Over: explicit keyboard instruction, bordered name field with visible placeholder, prominent Enter-to-save confirmation |
| [game-over-name-entered.png](game-over-name-entered.png) | `LOSSQA` visibly typed in the Game Over field, with a drawn caret |
| [game-over-saved-highscores.png](game-over-saved-highscores.png) | After Enter on Game Over, `LOSSQA` and its score appear in native Highscores |
| [victory-name-empty.png](victory-name-empty.png) | Victory: the same clearly visible input prompt and save action |
| [victory-name-entered.png](victory-name-entered.png) | `WINQA` visibly typed in the Victory field |
| [victory-saved-highscores.png](victory-saved-highscores.png) | After Enter on Victory, both `LOSSQA` and `WINQA` appear in native Highscores |

No mouse click on the drawn field is necessary: with the game window focused,
type the name directly. Backspace edits; Enter saves; Escape skips saving.

The game-over run was left stationary so the actual autonomous ghosts consumed
its lives. The victory run used the documented C/I/F and N/Enter evaluation
controls to complete ten levels. Both runs legitimately ended with score zero;
zero is a valid score, and no score was manufactured for screenshots. JSON on
disk was read back after saving to verify both submitted names and scores.

The process then exited through the real Exit menu; `make run` returned 0 without
a callback failure. Automated regressions also check the two outcome layouts,
visible entered text, small-window bounds, name filtering, save failures and retry.

## Earlier gameplay/lifecycle evidence

`fitted-menu.png`, `native-gameplay.png`, and `fitted-game-pause.png` show native
menu/gameplay/pause rendering. `native-victory.png`, `native-game-over.png`,
`native-name-entry.png`, and `native-highscores.png` capture the earlier terminal
layout before the field-visibility fix. They document the remediation history,
but the six screenshots above supersede them for name-entry acceptance.
