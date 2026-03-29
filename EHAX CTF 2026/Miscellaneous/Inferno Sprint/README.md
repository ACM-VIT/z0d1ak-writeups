# Inferno Sprint

| Field      | Value |
|------------|-------|
| Category   | Miscellaneous |
| Points     | 50 |
| Solves     | 353 |

## Description

`author: CyC`

The labyrinth burns. You have 90 seconds.
Survive 5 rounds of increasingly brutal fire mazes. Dodge multi-speed fires, use portals, and escape to any edge - before the flames consume you.
Good luck. The inferno waits for no one.

 `nc chall.ehax.in 31337 `

## Writeup

### Flag

```text
EH4X{1nf3rn0_spr1n7_bl4z3_runn3r_m4573r}
```

### Executive Summary

Each round is a pathfinding problem with time-dependent hazards. Fire sources spread at different speeds, so we first compute the earliest ignition time for every cell, then run a BFS for the player constrained by strict safety (`arrival_time < fire_time`). Portals are modeled as additional time-costing transitions.

### Vulnerability Analysis

The challenge is designed to punish greedy movement:

- Multiple fire rates (`1`, `2`, `3`) create non-uniform danger timing.
- Valid paths must satisfy both geometry and timing.
- Portal usage is optional but often necessary under move limits.

A static shortest-path algorithm fails; we need time-aware reachability.

### Exploit Strategy

1. Decode each hex row into ASCII grid cells.
2. Build a fire-time matrix:
   - Run multi-source BFS for each fire speed.
   - Convert graph distance to ignition turn via `distance * speed`.
   - Keep per-cell minimum across all fire groups.
3. Run player BFS from `START r c`:
   - Transitions: `W/A/S/D` plus portal move `P` when on `a`-`e`.
   - Only enter cells where `fire_time > player_time`.
   - Stop at first reachable edge cell with path length `<= LIMIT`.

### Implementation

Grid semantics used in solver:

- `#` wall, `.` free.
- `1`,`2`,`3` fire origins with spread period K.
- `a`-`e` paired portals, teleport costs one turn.

Complexity per round is linear in grid size (`O(H*W)` BFS passes), which is fast enough for all five rounds within the service timeout.

### Execution & Results

The scripted solver generated valid move strings for all five rounds and returned the final flag.

