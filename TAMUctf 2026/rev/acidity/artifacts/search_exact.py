#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from search_scripted import (
    SEARCH_ACTIONS,
    action_byte,
    capture_boards,
    insertion_indices,
    terrain_actions_from_genome,
    acid,
)


JUMP_SEQ = (-2, -1, 0, 1, 2)


@dataclass(frozen=True)
class ExactState:
    x: int
    y: int
    jump_idx: int
    fall_v: int
    pending: str


def parse_mods(spec: str):
    out = {}
    if not spec:
        return out
    for part in spec.split(","):
        if not part:
            continue
        pos_s, val_s = part.split("=")
        out[int(pos_s, 0)] = int(val_s, 0) & 0xFF
    return out


def build_genome(mods, frames):
    idxs = insertion_indices(frames)
    genome = [0] * len(idxs)
    for pos, value in mods.items():
        if pos in idxs:
            genome[idxs.index(pos)] = value
    return genome


def exact_step(board_next, state: ExactState, next_pending: str):
    x, y = state.x, state.y
    jump_idx = state.jump_idx
    fall_v = state.fall_v
    pending = state.pending

    dx = -1 if pending == "a" else 1 if pending == "d" else 0
    nx = x + dx
    if 0 <= nx < acid.COLS and board_next[y][nx] != "#":
        x = nx

    grounded = y + 1 < acid.ROWS and board_next[y + 1][x] == "#"
    next_jump_idx = jump_idx
    if jump_idx >= 0:
        delta = JUMP_SEQ[jump_idx]
        next_jump_idx = jump_idx + 1 if jump_idx + 1 < len(JUMP_SEQ) else -1
        fall_v = 0
    elif pending == "w" and grounded:
        delta = JUMP_SEQ[0]
        next_jump_idx = 1
        fall_v = 0
    elif not grounded:
        fall_v += 1
        delta = fall_v
    else:
        delta = 0
        fall_v = 0

    if delta < 0:
        for _ in range(-delta):
            if y - 1 < 0 or board_next[y - 1][x] == "#":
                next_jump_idx = -1
                break
            y -= 1
    elif delta > 0:
        moved = 0
        for _ in range(delta):
            if y + 1 >= acid.ROWS or board_next[y + 1][x] == "#":
                if jump_idx >= 0 or pending == "w":
                    next_jump_idx = -1
                fall_v = 0
                break
            y += 1
            moved += 1
        if moved < delta and jump_idx >= 0:
            next_jump_idx = -1

    return ExactState(
        x=x,
        y=y,
        jump_idx=next_jump_idx,
        fall_v=fall_v,
        pending=next_pending,
    )


def score_best(best):
    return (
        1 if best["found"] else 0,
        -best["distance"],
        best["y"],
        -abs(best["x"] - 17),
        -best["frame"],
    )


def evaluate_mods(mods, frames=103):
    genome = build_genome(mods, frames)
    terrain_actions = terrain_actions_from_genome(genome, frames)
    raw = capture_boards(terrain_actions, frames, speed_div=1000, read_timeout=1.0)
    if len(raw) < 2:
        return None

    boards = [acid.normalize_board(board) for board in raw]
    start = acid.find_player(raw[0])
    if start is None:
        return None

    ins = set(insertion_indices(len(boards)))
    start_state = ExactState(x=start[0], y=start[1], jump_idx=-1, fall_v=0, pending="")
    layer = {start_state: b""}
    seen = {(0, start_state)}
    best = {
        "found": False,
        "distance": abs(start[0] - 17) + abs(start[1] - 24),
        "frame": 0,
        "x": start[0],
        "y": start[1],
        "full_actions": b"",
    }

    for t in range(len(boards) - 1):
        nxt = {}
        choices = [terrain_actions[t]] if t in ins else SEARCH_ACTIONS
        for state, full_actions in layer.items():
            for action in choices:
                ns = exact_step(boards[t + 1], state, action)
                next_full = full_actions + bytes([action_byte(action)])
                if acid.board_char(raw[t + 1], ns.x, ns.y) == "F":
                    return {
                        "found": True,
                        "distance": 0,
                        "frame": t + 1,
                        "x": ns.x,
                        "y": ns.y,
                        "full_actions": next_full,
                        "mods": dict(mods),
                    }
                dist = abs(ns.x - 17) + abs(ns.y - 24)
                candidate = {
                    "found": False,
                    "distance": dist,
                    "frame": t + 1,
                    "x": ns.x,
                    "y": ns.y,
                    "full_actions": next_full,
                    "mods": dict(mods),
                }
                if score_best(candidate) > score_best(best):
                    best = candidate
                key = (t + 1, ns)
                if key not in seen:
                    seen.add(key)
                    nxt[ns] = next_full
        layer = nxt
        if not layer:
            break
    return best


def print_best(best):
    print(
        f"found={best['found']} distance={best['distance']} frame={best['frame']} "
        f"x={best['x']} y={best['y']}"
    )
    nonzero_mods = {pos: hex(val) for pos, val in sorted(best["mods"].items()) if val}
    print(f"mods={nonzero_mods}")
    moves = [(i, hex(b)) for i, b in enumerate(best["full_actions"]) if b]
    print(f"moves={moves}")


def cmd_eval(args):
    best = evaluate_mods(parse_mods(args.mods), args.frames)
    if best is None:
        raise SystemExit("evaluation failed")
    print_best(best)


def cmd_scan_slot(args):
    base_mods = parse_mods(args.mods)
    top = []

    def one(value):
        mods = dict(base_mods)
        mods[args.pos] = value
        best = evaluate_mods(mods, args.frames)
        return value, best

    values = list(range(256))
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for value, best in ex.map(one, values):
            if best is None:
                continue
            top.append((score_best(best), value, best))
    top.sort(reverse=True)
    for score, value, best in top[: args.top]:
        print(f"value={hex(value)} score={score}")
        print_best(best)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)

    pe = sp.add_parser("eval")
    pe.add_argument("--frames", type=int, default=103)
    pe.add_argument("--mods", default="")
    pe.set_defaults(func=cmd_eval)

    ps = sp.add_parser("scan-slot")
    ps.add_argument("--frames", type=int, default=103)
    ps.add_argument("--mods", default="")
    ps.add_argument("--pos", type=int, required=True)
    ps.add_argument("--workers", type=int, default=6)
    ps.add_argument("--top", type=int, default=20)
    ps.set_defaults(func=cmd_scan_slot)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
