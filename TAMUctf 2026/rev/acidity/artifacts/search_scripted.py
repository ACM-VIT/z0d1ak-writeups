#!/usr/bin/env python3
import argparse
import fcntl
import importlib.util
import os
import random
import select
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOLVE_PY = ROOT / "solve.py"
HOOK_SO = ROOT / "hook_script.so"
CONTAINER_NAME = os.environ.get("ACID_CONTAINER")

spec = importlib.util.spec_from_file_location("acid_solve", SOLVE_PY)
acid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acid)

DEFAULT_TERRAIN_BYTES = [
    0x00,
    0x01,
    0x09,
    0x0A,
    0x1B,
    0x20,
    0x30,
    0x41,
    0x61,  # a
    0x64,  # d
    0x77,  # w
    0x78,  # x
    0x73,  # s
    0x7F,
    0xFF,
]
SEARCH_ACTIONS = ("", "a", "d", "w")


def action_byte(action):
    return 0 if action == "" else ord(action)


def byte_action(value):
    return "" if value == 0 else bytes([value]).decode("latin1")


def script_hex(actions):
    # The binary consumes one "current input" before the first visible frame.
    seq = [""] + actions
    return "".join("00" if a == "" else f"{ord(a):02x}" for a in seq)


def capture_boards(actions, frames, speed_div=100, read_timeout=3.0):
    if CONTAINER_NAME:
        cmd = [
            "docker",
            "exec",
            "-i",
            CONTAINER_NAME,
            "env",
            "LD_PRELOAD=/work/hook_script.so",
            f"ACID_SPEED_DIV={speed_div}",
            f"ACID_SCRIPT_HEX={script_hex(actions)}",
            "./acidity",
        ]
    else:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--platform",
            "linux/amd64",
            "-v",
            f"{ROOT}:/work",
            "-v",
            f"{HOOK_SO}:/hook_script.so:ro",
            "-e",
            "LD_PRELOAD=/hook_script.so",
            "-e",
            f"ACID_SPEED_DIV={speed_div}",
            "-e",
            f"ACID_SCRIPT_HEX={script_hex(actions)}",
            "-w",
            "/work",
            "ubuntu:24.04",
            "./acidity",
        ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    fd = proc.stdout.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    buf = b""
    raw = []
    while len(raw) < frames:
        if acid.MARKER not in buf:
            r, _, _ = select.select([fd], [], [], read_timeout)
            if not r:
                break
            try:
                chunk = os.read(fd, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                break
            buf += chunk
            continue
        idx = buf.index(acid.MARKER)
        frame = buf[:idx]
        buf = buf[idx + len(acid.MARKER):]
        board = acid.extract_board(frame)
        if board is not None:
            raw.append(tuple(board))
    proc.kill()
    return raw


def insertion_indices(frames):
    return list(range(2, frames, 4))


def terrain_actions_from_genome(genome, frames):
    actions = [""] * frames
    for idx, byte in zip(insertion_indices(frames), genome):
        actions[idx] = byte_action(byte)
    return actions


def merge_actions(terrain_actions, full_action_bytes):
    ins = set(insertion_indices(len(terrain_actions)))
    out = terrain_actions[:]
    for i, value in enumerate(full_action_bytes):
        if i >= len(out) or i in ins:
            continue
        out[i] = byte_action(value)
    return out


def flag_clearance(board, x=17):
    depth = 0
    for y in range(acid.ROWS - 1, -1, -1):
        if acid.board_char(board, x, y) == "#":
            break
        depth += 1
    return depth


def evaluate_genome(genome, frames, speed_div=100, read_timeout=3.0):
    terrain_actions = terrain_actions_from_genome(genome, frames)
    raw = capture_boards(terrain_actions, frames, speed_div=speed_div, read_timeout=read_timeout)
    if len(raw) < 2:
        return None

    boards = [acid.normalize_board(b) for b in raw]
    start_pos = acid.find_player(raw[0])
    if start_pos is None:
        return None

    ins = set(insertion_indices(len(boards)))
    start = acid.SearchState(x=start_pos[0], y=start_pos[1], jump_idx=-1, pending="")
    clearances = [flag_clearance(board) for board in boards]
    layer = {start: b""}
    seen = {(0, start)}
    best = {
        "max_y": start.y,
        "frame": 0,
        "x": start.x,
        "full_actions": b"",
    }
    best_flag = {
        "distance": abs(start.x - 17) + max(0, 23 - start.y),
        "frame": 0,
        "x": start.x,
        "y": start.y,
        "full_actions": b"",
    }

    for t, board in enumerate(boards[:-1]):
        nxt = {}
        choices = [terrain_actions[t]] if t in ins else SEARCH_ACTIONS
        for state, full_actions in layer.items():
            for action in choices:
                ns = acid.search_step(board, state, action)
                if ns is None:
                    continue
                next_actions = full_actions + bytes([action_byte(action)])
                if ns.y > best["max_y"]:
                    best = {
                        "max_y": ns.y,
                        "frame": t + 1,
                        "x": ns.x,
                        "full_actions": next_actions,
                    }
                dist = abs(ns.x - 17) + max(0, 23 - ns.y)
                if (
                    dist < best_flag["distance"]
                    or (dist == best_flag["distance"] and ns.y > best_flag["y"])
                    or (
                        dist == best_flag["distance"]
                        and ns.y == best_flag["y"]
                        and abs(ns.x - 17) < abs(best_flag["x"] - 17)
                    )
                ):
                    best_flag = {
                        "distance": dist,
                        "frame": t + 1,
                        "x": ns.x,
                        "y": ns.y,
                        "full_actions": next_actions,
                    }
                if acid.board_char(boards[t + 1], ns.x, ns.y) == "F":
                    full = merge_actions(terrain_actions, next_actions)
                    return {
                        "found": True,
                        "boards": raw,
                        "flag_clearance": max(clearances),
                        "terrain_actions": terrain_actions,
                        "full_actions": full,
                        "best": {
                            "max_y": ns.y,
                            "frame": t + 1,
                            "x": ns.x,
                            "full_actions": next_actions,
                        },
                        "best_flag": {
                            "distance": 0,
                            "frame": t + 1,
                            "x": ns.x,
                            "y": ns.y,
                            "full_actions": next_actions,
                        },
                    }
                key = (t + 1, ns)
                if key not in seen:
                    seen.add(key)
                    nxt[ns] = next_actions
        layer = nxt
        if not layer:
            break

    return {
        "found": False,
        "boards": raw,
        "flag_clearance": max(clearances),
        "terrain_actions": terrain_actions,
        "full_actions": None,
        "best": best,
        "best_flag": best_flag,
    }


def score_key(result, mode="depth"):
    best = result["best"]
    if mode == "flag":
        best_flag = result["best_flag"]
        return (
            1 if result["found"] else 0,
            result["flag_clearance"],
            -best_flag["distance"],
            best_flag["y"],
            -abs(best_flag["x"] - 17),
            best["max_y"],
            -best["frame"],
        )
    # Prefer deeper rows, then closeness to the flag column, then earlier depth.
    return (
        1 if result["found"] else 0,
        best["max_y"],
        -abs(best["x"] - 17),
        -best["frame"],
    )


def format_actions(actions):
    out = []
    if isinstance(actions, (bytes, bytearray)):
        seq = [byte_action(value) for value in actions]
    else:
        seq = actions
    for ch in seq:
        if ch == "":
            out.append(".")
        elif ch in "adwq":
            out.append(ch)
        else:
            out.append(f"\\x{ord(ch):02x}")
    return "".join(out)


def mutate(genome, terrain_bytes, rnd):
    out = genome[:]
    count = rnd.randint(1, 3)
    for _ in range(count):
        i = rnd.randrange(len(out))
        out[i] = rnd.choice(terrain_bytes)
    return out


def parse_genome(spec, expected_len):
    if spec is None:
        return None
    genome = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        genome.append(int(part, 0) & 0xFF)
    if len(genome) != expected_len:
        raise ValueError(f"expected {expected_len} genome entries, got {len(genome)}")
    return genome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--coord-sweeps", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--speed-div", type=int, default=100)
    ap.add_argument("--read-timeout", type=float, default=3.0)
    ap.add_argument("--terrain-bytes", default=None,
                    help="comma-separated byte values in decimal or hex, e.g. 0,0x20,0x78")
    ap.add_argument("--start-genome", default=None,
                    help="comma-separated byte values for the insertion genome")
    ap.add_argument("--score-mode", choices=("depth", "flag"), default="depth")
    args = ap.parse_args()

    if args.terrain_bytes:
        terrain_bytes = []
        for part in args.terrain_bytes.split(","):
            part = part.strip()
            if not part:
                continue
            terrain_bytes.append(int(part, 0) & 0xFF)
    else:
        terrain_bytes = DEFAULT_TERRAIN_BYTES

    ins_count = len(insertion_indices(args.frames))
    rnd = random.Random(args.seed)

    try:
        genome = parse_genome(args.start_genome, ins_count)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if genome is None:
        genome = [0] * ins_count

    cache = {}

    def eval_cached(candidate):
        key = tuple(candidate)
        if key not in cache:
            cache[key] = evaluate_genome(
                list(key),
                args.frames,
                speed_div=args.speed_div,
                read_timeout=args.read_timeout,
            )
        return cache[key]

    best_result = eval_cached(genome)
    if best_result is None:
        raise SystemExit("failed to capture baseline boards")

    print(
        f"baseline max_y={best_result['best']['max_y']} "
        f"frame={best_result['best']['frame']} x={best_result['best']['x']} "
        f"flag_clear={best_result['flag_clearance']} "
        f"flag_dist={best_result['best_flag']['distance']}"
    )

    for it in range(1, args.iters + 1):
        cand = mutate(genome, terrain_bytes, rnd)
        result = eval_cached(cand)
        if result is None:
            continue
        if score_key(result, mode=args.score_mode) > score_key(best_result, mode=args.score_mode):
            genome = cand
            best_result = result
            print(
                f"iter={it} max_y={result['best']['max_y']} "
                f"frame={result['best']['frame']} x={result['best']['x']} "
                f"flag_clear={result['flag_clearance']} "
                f"flag_dist={result['best_flag']['distance']} "
                f"terrain={','.join(hex(x) for x in genome)}"
            )
        if result["found"]:
            print("FOUND")
            print("terrain_actions", format_actions(result["terrain_actions"]))
            print("full_actions", format_actions(result["full_actions"]))
            return 0

    for sweep in range(1, args.coord_sweeps + 1):
        improved = False
        for idx in range(ins_count):
            best_byte = genome[idx]
            sweep_best = best_result
            for value in terrain_bytes:
                if value == genome[idx]:
                    continue
                cand = genome[:]
                cand[idx] = value
                result = eval_cached(cand)
                if result is None:
                    continue
                if score_key(result, mode=args.score_mode) > score_key(sweep_best, mode=args.score_mode):
                    best_byte = value
                    sweep_best = result
            if best_byte != genome[idx]:
                genome[idx] = best_byte
                best_result = sweep_best
                improved = True
                print(
                    f"coord sweep={sweep} idx={idx} max_y={best_result['best']['max_y']} "
                    f"frame={best_result['best']['frame']} x={best_result['best']['x']} "
                    f"flag_clear={best_result['flag_clearance']} "
                    f"flag_dist={best_result['best_flag']['distance']} "
                    f"terrain={','.join(hex(x) for x in genome)}"
                )
                if best_result["found"]:
                    print("FOUND")
                    print("terrain_actions", format_actions(best_result["terrain_actions"]))
                    print("full_actions", format_actions(best_result["full_actions"]))
                    return 0
        if not improved:
            break

    print("best terrain_actions", format_actions(best_result["terrain_actions"]))
    if best_result["best"]["full_actions"]:
        print("best full_actions", format_actions(merge_actions(
            best_result["terrain_actions"],
            best_result["best"]["full_actions"],
        )))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
