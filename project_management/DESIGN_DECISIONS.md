# Design Decisions

## Separate gameplay from rendering

`GameSession` owns gameplay rules and mutable game state, while `GameScreen` converts input into session commands and renders session state. This keeps game logic testable without opening an MLX window.

## Adapt the assigned maze generator instead of replacing it

`src/maze.py` wraps the assigned A-Maze-ing package and calls it with `perfect=False`. The package is treated as an external dependency and is not modified.

The first level uses the configured fixed seed. Later levels use newly generated random seeds.

## Continuous cell-space movement

Actor positions are stored as floating-point cell coordinates. Movement is subdivided into small simulation steps and stops at cell centers when necessary. This allows queued turns, reliable pacgum collection, and collision checking without tying game behavior to frame count.

## Simple, explainable ghost AI

At intersections, ghosts evaluate legal neighboring cells using distance to the player:

- normal ghosts prefer moves that reduce distance;
- edible ghosts prefer moves that increase distance;
- direct reversal is avoided when another legal move exists.

This satisfies the required chase/flee behavior while remaining easy to explain and test.

## Swept collision detection

Collision logic considers movement during a simulation step rather than only final positions. This prevents fast actors from passing through each other between frames.

## Pacgum placement

`pacgum = 0` means normal pacgums fill all eligible reachable corridor cells except the player start and power-pellet cells. A positive value requests a sampled count and is clamped to the available capacity.

Power pellets are placed at reachable cells nearest the four maze corners.

## Level completion

A level completes after all normal pacgums and power pellets have been consumed. Score and remaining lives carry to the next level.

The current timeout policy is game over when the level timer reaches zero.

## Persistent highscores

Highscores are stored locally as JSON. Only valid entries are accepted, results are sorted and limited to the top ten, and saving uses a temporary file followed by atomic replacement so a failed write does not destroy the previous table.

## Robust configuration

Configuration values are validated independently. Missing or invalid values fall back to safe defaults with a clear message, and unknown keys are ignored. This allows evaluators to modify the configuration without causing a traceback.

## UI dimensions

The current normal window size is `1280 x 800`. Rendering code also fits oversized requested windows to the available display so the interface remains usable on smaller screens.
