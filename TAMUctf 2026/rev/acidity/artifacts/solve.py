#!/usr/bin/env python3
import argparse
import fcntl
import os
import re
import ssl
import socket
import subprocess
import sys
import select
from dataclasses import dataclass
from pathlib import Path


MARKER = b"Move: [a] left, [d] right, [w] jump, [q] quit\r\n"
ANSI_RE = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")
ROWS = 25
COLS = 35
FLAG_ROW = 24


def strip_ansi(data: bytes) -> str:
    clean = ANSI_RE.sub(b"", data).replace(b"\r", b"")
    return clean.decode("latin1", "ignore")


def extract_board(frame: bytes):
    text = strip_ansi(frame)
    lines = [line for line in text.split("\n") if line]
    if len(lines) < ROWS:
        return None
    board = lines[-ROWS:]
    if len(board) != ROWS:
        return None
    return board


def find_player(board):
    for y, row in enumerate(board):
        x = row.find("@")
        if x != -1:
            return x, y
    return None


def normalize_board(board):
    out = []
    for row in board:
        row = row.replace("@", " ")
        out.append(row)
    return tuple(out)


class LocalGame:
    def __init__(self, root: Path):
        self.root = root
        container_name = os.environ.get("ACID_CONTAINER")
        preload = os.environ.get("ACID_PRELOAD")
        self.cmd = ["docker"]
        if container_name:
            self.cmd.extend(["exec", "-i", container_name, "env"])
            if preload:
                preload_path = Path(preload).resolve()
                try:
                    rel = preload_path.relative_to(root.resolve())
                except ValueError:
                    raise RuntimeError(f"ACID_PRELOAD must live under {root} when using ACID_CONTAINER")
                self.cmd.append(f"LD_PRELOAD=/work/{rel.as_posix()}")
            self.cmd.append("./acidity")
        else:
            self.cmd.extend([
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/amd64",
            ])
            if preload:
                self.cmd.extend(["-v", f"{preload}:/libspeed.so:ro", "-e", "LD_PRELOAD=/libspeed.so"])
            self.cmd.extend([
                "-v",
                f"{root}:/work",
                "-w",
                "/work",
                "ubuntu:24.04",
                "./acidity",
            ])
        self.proc = None
        self.buf = b""
        self.frames = 0

    def __enter__(self):
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        fd = self.proc.stdout.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if self.proc is not None:
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass
            self.proc = None

    def next_frame(self):
        while True:
            if MARKER not in self.buf:
                fd = self.proc.stdout.fileno()
                ready, _, _ = select.select([fd], [], [], 60.0)
                if not ready:
                    return None
                try:
                    chunk = os.read(fd, 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    return None
                self.buf += chunk
            if MARKER in self.buf:
                idx = self.buf.index(MARKER)
                frame = self.buf[:idx]
                self.buf = self.buf[idx + len(MARKER):]
                board = extract_board(frame)
                if board is None:
                    continue
                self.frames += 1
                return board

    def send(self, action: str):
        if self.proc.stdin is None:
            raise RuntimeError("stdin closed")
        if action:
            self.proc.stdin.write(action.encode("latin1"))
            self.proc.stdin.flush()


class RemoteGame:
    def __init__(self, host: str, port: int, sni: str):
        self.host = host
        self.port = port
        self.sni = sni
        self.sock = None
        self.buf = b""
        self.frames = 0

    def __enter__(self):
        ctx = ssl._create_unverified_context()
        raw = socket.create_connection((self.host, self.port))
        self.sock = ctx.wrap_socket(raw, server_hostname=self.sni)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def next_frame(self):
        while True:
            if MARKER in self.buf:
                idx = self.buf.index(MARKER)
                frame = self.buf[:idx]
                self.buf = self.buf[idx + len(MARKER):]
                board = extract_board(frame)
                if board is None:
                    continue
                self.frames += 1
                return board
            data = self.sock.recv(4096)
            if not data:
                return None
            self.buf += data

    def send(self, action: str):
        if action:
            self.sock.sendall(action.encode("latin1"))


@dataclass(frozen=True)
class State:
    x: int
    y: int
    vy: int


@dataclass(frozen=True)
class SearchState:
    x: int
    y: int
    jump_idx: int
    pending: str


def board_char(board, x, y):
    if x < 0 or x >= COLS or y < 0 or y >= ROWS:
        return "#"
    return board[y][x]


def is_solid(board, x, y):
    return board_char(board, x, y) == "#"


def is_deadly(board, x, y):
    ch = board_char(board, x, y)
    return ch == "|" or (y >= 0 and y < ROWS and ch == "#")


def locate_flag(board):
    for y, row in enumerate(board):
        x = row.find("F")
        if x != -1:
            return x, y
    return None


def parse_actions(spec: str):
    mapping = {".": "", "_": "", "-": "", "a": "a", "d": "d", "w": "w", "q": "q"}
    return [mapping[ch] for ch in spec]


def build_insertion_action_stream(spec: str):
    actions = []
    for i, ch in enumerate(spec):
        if i == 0:
            actions.extend(["", "", parse_actions(ch)[0]])
        else:
            actions.extend(["", "", "", parse_actions(ch)[0]])
    return actions


def transition(board, state: State, action: str):
    x, y, vy = state.x, state.y, state.vy
    dx = -1 if action == "a" else 1 if action == "d" else 0

    on_ground = is_solid(board, x, y + 1)
    if action == "w" and on_ground and vy == 0:
        vy = -3

    nx = x + dx
    if not is_solid(board, nx, y):
        x = nx

    if vy < 0:
        steps = -vy
        for _ in range(steps):
            if is_solid(board, x, y - 1):
                vy = 0
                break
            y -= 1
        vy += 1
    else:
        if not is_solid(board, x, y + 1):
            y += 1
            vy = min(vy + 1, 3)
        else:
            vy = 0

    if y < 0:
        y = 0
        vy = max(vy, 0)

    if y >= ROWS:
        return None
    if board_char(board, x, y) == "|":
        return None
    return State(x, y, vy)


JUMP_SEQ = (-2, -1, 0, 1, 2)
SEARCH_ACTIONS = ("", "a", "d", "w")


def is_dead(board, x, y):
    ch = board_char(board, x, y)
    return ch == "|"


def apply_vertical_delta(board, x, y, delta):
    if delta == 0:
        return x, y, False
    step = -1 if delta < 0 else 1
    for _ in range(abs(delta)):
        ny = y + step
        if is_solid(board, x, ny):
            return x, y, True
        if is_dead(board, x, ny):
            return None
        y = ny
    return x, y, False


def search_step(board, state: SearchState, next_pending: str):
    x, y, jump_idx, pending = state.x, state.y, state.jump_idx, state.pending

    if is_dead(board, x, y):
        return None

    dx = -1 if pending == "a" else 1 if pending == "d" else 0
    if dx:
        nx = x + dx
        if not is_solid(board, nx, y):
            x = nx
            if is_dead(board, x, y):
                return None

    next_jump_idx = jump_idx
    if jump_idx >= 0:
        delta = JUMP_SEQ[jump_idx]
        next_jump_idx = jump_idx + 1 if jump_idx + 1 < len(JUMP_SEQ) else -1
    elif pending == "w" and is_solid(board, x, y + 1):
        delta = JUMP_SEQ[0]
        next_jump_idx = 1
    elif not is_solid(board, x, y + 1):
        delta = 1
    else:
        delta = 0

    moved = apply_vertical_delta(board, x, y, delta)
    if moved is None:
        return None
    x, y, collided = moved

    # Hitting the ceiling or landing during a jump ends the current arc.
    if jump_idx >= 0 and collided:
        next_jump_idx = -1
    elif pending == "w" and delta < 0 and collided:
        next_jump_idx = -1
    elif jump_idx >= 0 and delta > 0 and collided:
        next_jump_idx = -1

    return SearchState(x=x, y=y, jump_idx=next_jump_idx, pending=next_pending)


def capture_boards(root: Path, frames: int):
    raw_boards = []
    boards = []
    with LocalGame(root) as game:
        for _ in range(frames):
            board = game.next_frame()
            if board is None:
                break
            raw_boards.append(tuple(board))
            boards.append(normalize_board(board))
    return raw_boards, boards


def actual_trace(root: Path, actions, frames):
    out = []
    with LocalGame(root) as game:
        for i in range(frames):
            board = game.next_frame()
            if board is None:
                break
            out.append(find_player(board))
            action = actions[i] if i < len(actions) else ""
            game.send(action)
    return out


def model_trace(boards, start_pos, actions):
    state = SearchState(x=start_pos[0], y=start_pos[1], jump_idx=-1, pending="")
    out = [(state.x, state.y)]
    for i, board in enumerate(boards[:-1]):
        action = actions[i] if i < len(actions) else ""
        state = search_step(board, state, action)
        if state is None:
            out.append(None)
            break
        out.append((state.x, state.y))
    return out


def shortest_path(boards, start, actions=("","a","d","w")):
    flag_pos = locate_flag(boards[-1])
    if flag_pos is None:
        raise RuntimeError("flag not found on final board")

    seen = {start: ""}
    layer = {start: ""}
    for t, board in enumerate(boards, 1):
        nxt = {}
        for state, path in layer.items():
            for action in actions:
                ns = transition(board, state, action)
                if ns is None:
                    continue
                if board_char(board, ns.x, ns.y) == "F":
                    return path + action
                if ns not in seen:
                    out = path + action
                    seen[ns] = out
                    nxt[ns] = out
        layer = nxt
        if not layer:
            break
    return None


def capture_sequence(game_factory, actions, strip_player=False):
    boards = []
    with game_factory() as game:
        for action in actions:
            board = game.next_frame()
            if board is None:
                break
            boards.append(normalize_board(board) if strip_player else tuple(board))
            if action is not None:
                game.send(action)
        board = game.next_frame()
        if board is not None:
            boards.append(normalize_board(board) if strip_player else tuple(board))
    return boards


def cmd_compare(args):
    root = Path(args.root)

    def gf():
        return LocalGame(root)

    actions_a = parse_actions(args.actions_a)
    actions_b = parse_actions(args.actions_b)
    if len(actions_a) < args.frames:
        actions_a.extend([""] * (args.frames - len(actions_a)))
    if len(actions_b) < args.frames:
        actions_b.extend([""] * (args.frames - len(actions_b)))

    a = capture_sequence(gf, actions_a[:args.frames], strip_player=True)
    b = capture_sequence(gf, actions_b[:args.frames], strip_player=True)
    print(f"frames_a={len(a)} frames_b={len(b)}")
    for i, (ba, bb) in enumerate(zip(a, b), 1):
        same = ba == bb
        print(f"frame {i} same={same}")
        if not same:
            for row, (ra, rb) in enumerate(zip(ba, bb)):
                if ra != rb:
                    print(f" row={row}")
                    print(ra)
                    print(rb)
                    return 1
    return 0


def cmd_dump(args):
    root = Path(args.root)
    with LocalGame(root) as game:
        for i in range(args.frames):
            board = game.next_frame()
            if board is None:
                print(f"EOF at frame {i}")
                break
            print(f"FRAME {i + 1}")
            print("\n".join(board))
            print()
            game.send(args.action if args.action is not None else "")
    return 0


def cmd_trace(args):
    root = Path(args.root)
    actions = parse_actions(args.actions)
    with LocalGame(root) as game:
        frame = 0
        while frame < args.frames:
            board = game.next_frame()
            if board is None:
                print(f"EOF at frame {frame}")
                break
            frame += 1
            pos = find_player(board)
            below = None
            if pos is not None and pos[1] + 1 < ROWS:
                below = board[pos[1] + 1][pos[0]]
            print(f"frame={frame} pos={pos} below={below}")
            if args.show:
                print("\n".join(board))
                print()
            action = actions[frame - 1] if frame - 1 < len(actions) else ""
            game.send(action)
    return 0


def cmd_rows(args):
    root = Path(args.root)
    actions = parse_actions(args.actions)
    with LocalGame(root) as game:
        for frame in range(1, args.frames + 1):
            board = game.next_frame()
            if board is None:
                print(f"EOF at frame {frame - 1}")
                break
            print(f"FRAME {frame}")
            for row in board[:args.top]:
                print(row)
            print()
            action = actions[frame - 1] if frame - 1 < len(actions) else ""
            game.send(action)
    return 0


def cmd_probe(args):
    root = Path(args.root)
    actions = build_insertion_action_stream(args.ins_actions)
    with LocalGame(root) as game:
        for frame in range(1, args.frames + 1):
            board = game.next_frame()
            if board is None:
                print(f"EOF at frame {frame - 1}")
                break
            if frame >= 4 and frame % 4 == 0:
                idx = frame // 4
                print(f"insert {idx}: {board[0]}")
            action = actions[frame - 1] if frame - 1 < len(actions) else ""
            game.send(action)
    return 0


def cmd_search(args):
    root = Path(args.root)
    raw_boards, boards = capture_boards(root, args.frames)
    print(f"captured={len(boards)}")
    if not boards:
        return 1

    initial_player = find_player(raw_boards[0]) if raw_boards else None
    if initial_player is None:
        print("failed to capture initial player")
        return 1

    flag_pos = locate_flag(boards[-1])
    if flag_pos is None:
        print("flag not found")
        return 1

    cur = {
        SearchState(x=initial_player[0], y=initial_player[1], jump_idx=-1, pending=""): ""
    }
    best = max(cur, key=lambda s: s.y)
    best_path = ""

    for frame_idx, board in enumerate(boards[:-1], 1):
        nxt = {}
        for state, path in cur.items():
            for action in SEARCH_ACTIONS:
                ns = search_step(board, state, action)
                if ns is None:
                    continue
                new_path = path + (action if action else ".")
                if (ns.x, ns.y) == flag_pos:
                    print(f"solved_at_frame={frame_idx + 1}")
                    print(new_path)
                    return 0
                if ns not in nxt:
                    nxt[ns] = new_path
                    if ns.y > best.y:
                        best = ns
                        best_path = new_path
        print(f"frame={frame_idx} states={len(nxt)} best_y={best.y}")
        cur = nxt
        if not cur:
            break

    print("no solution")
    print(f"best=({best.x},{best.y}) jump_idx={best.jump_idx} pending={best.pending!r}")
    print(best_path)
    return 1


def cmd_check(args):
    root = Path(args.root)
    actions = parse_actions(args.actions)
    raw_boards, boards = capture_boards(root, max(args.frames, len(actions) + 1))
    if not raw_boards:
        print("failed to capture boards")
        return 1
    start_pos = find_player(raw_boards[0])
    actual = actual_trace(root, actions, args.frames)
    model = model_trace(boards[:args.frames], start_pos, actions)
    count = min(len(actual), len(model))
    for i in range(count):
        print(f"frame={i + 1} actual={actual[i]} model={model[i]}")
        if actual[i] != model[i]:
            return 1
    if len(actual) != len(model):
        print(f"length actual={len(actual)} model={len(model)}")
        return 1
    return 0


def cmd_run_remote(args):
    actions = list(args.actions)
    with RemoteGame(args.host, args.port, args.sni) as game:
        while True:
            board = game.next_frame()
            if board is None:
                print("EOF")
                return 0
            pos = find_player(board)
            print(f"frame={game.frames} pos={pos}")
            if args.show:
                print("\n".join(board))
                print()
            action = actions.pop(0) if actions else ""
            game.send(action)


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent),
        help="challenge directory with acidity binary",
    )
    sp = p.add_subparsers(dest="cmd", required=True)

    c = sp.add_parser("compare")
    c.add_argument("--frames", type=int, default=10)
    c.add_argument("--actions-a", default="")
    c.add_argument("--actions-b", default="d")
    c.set_defaults(func=cmd_compare)

    d = sp.add_parser("dump")
    d.add_argument("--frames", type=int, default=5)
    d.add_argument("--action", default="")
    d.set_defaults(func=cmd_dump)

    t = sp.add_parser("trace")
    t.add_argument("--frames", type=int, default=12)
    t.add_argument("--actions", default="")
    t.add_argument("--show", action="store_true")
    t.set_defaults(func=cmd_trace)

    rr = sp.add_parser("rows")
    rr.add_argument("--frames", type=int, default=8)
    rr.add_argument("--actions", default="")
    rr.add_argument("--top", type=int, default=4)
    rr.set_defaults(func=cmd_rows)

    pr = sp.add_parser("probe")
    pr.add_argument("--frames", type=int, default=20)
    pr.add_argument("--ins-actions", default=".")
    pr.set_defaults(func=cmd_probe)

    s = sp.add_parser("search")
    s.add_argument("--frames", type=int, default=103)
    s.set_defaults(func=cmd_search)

    c = sp.add_parser("check")
    c.add_argument("--frames", type=int, default=20)
    c.add_argument("--actions", default="")
    c.set_defaults(func=cmd_check)

    r = sp.add_parser("remote")
    r.add_argument("--host", default="streams.tamuctf.com")
    r.add_argument("--port", type=int, default=443)
    r.add_argument("--sni", default="acidity")
    r.add_argument("--actions", default="")
    r.add_argument("--show", action="store_true")
    r.set_defaults(func=cmd_run_remote)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
