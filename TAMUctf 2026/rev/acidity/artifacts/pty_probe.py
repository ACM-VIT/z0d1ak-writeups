#!/usr/bin/env python3
import argparse
import os
import pty
import re
import select
import socket
import ssl
import subprocess
import time
from pathlib import Path


MARKER = b"Move: [a] left, [d] right, [w] jump, [q] quit\r\r\n"
ANSI_RE = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]")
FLAG_RE = re.compile(r"gigem\{[^}]+\}")


def strip_ansi(data: bytes) -> str:
    return ANSI_RE.sub(b"", data).replace(b"\r", b"").decode("latin1", "ignore")


def extract_board(frame: bytes):
    text = strip_ansi(frame)
    lines = [line for line in text.split("\n") if line]
    if len(lines) < 25:
        return None
    return lines[-25:]


def find_player(board):
    if board is None:
        return None
    for y, row in enumerate(board):
        x = row.find("@")
        if x != -1:
            return x, y
    return None


class PtyGame:
    def __init__(self, container="acid_runner"):
        self.container = container
        self.master = None
        self.proc = None
        self.buf = b""
        self.transcript = b""

    def __enter__(self):
        master, slave = pty.openpty()
        self.master = master
        self.proc = subprocess.Popen(
            ["docker", "exec", "-it", self.container, "./acidity"],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
        )
        os.close(slave)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.proc is not None:
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass
        if self.master is not None:
            try:
                os.close(self.master)
            except OSError:
                pass

    def next_frame(self, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            if MARKER in self.buf:
                idx = self.buf.index(MARKER)
                frame = self.buf[:idx]
                self.buf = self.buf[idx + len(MARKER):]
                board = extract_board(frame)
                if board is not None:
                    return board
            ready, _, _ = select.select([self.master], [], [], 0.2)
            if not ready:
                continue
            chunk = os.read(self.master, 65536)
            if not chunk:
                return None
            self.buf += chunk
            self.transcript += chunk
        return None

    def send(self, chars: str):
        os.write(self.master, chars.encode("latin1"))


class RemoteGame:
    def __init__(self, host: str, port: int, sni: str):
        self.host = host
        self.port = port
        self.sni = sni
        self.sock = None
        self.buf = b""
        self.transcript = b""

    def __enter__(self):
        ctx = ssl._create_unverified_context()
        raw = socket.create_connection((self.host, self.port))
        self.sock = ctx.wrap_socket(raw, server_hostname=self.sni)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass

    def next_frame(self, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            if b"Move: [a] left, [d] right, [w] jump, [q] quit\r\n" in self.buf:
                marker = b"Move: [a] left, [d] right, [w] jump, [q] quit\r\n"
                idx = self.buf.index(marker)
                frame = self.buf[:idx]
                self.buf = self.buf[idx + len(marker):]
                board = extract_board(frame)
                if board is not None:
                    return board
            ready, _, _ = select.select([self.sock], [], [], 0.2)
            if not ready:
                continue
            chunk = self.sock.recv(65536)
            if not chunk:
                return None
            self.buf += chunk
            self.transcript += chunk
        return None

    def send(self, chars: str):
        self.sock.sendall(chars.encode("latin1"))


class PipeGame:
    def __init__(self, root: Path):
        self.root = root
        self.proc = None
        self.buf = b""
        self.transcript = b""

    def __enter__(self):
        self.proc = subprocess.Popen(
            [
                "docker",
                "exec",
                "-i",
                "acid_runner",
                "./acidity",
            ],
            cwd=self.root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.proc is not None:
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass

    def next_frame(self, timeout=5.0):
        marker = b"Move: [a] left, [d] right, [w] jump, [q] quit\r\n"
        end = time.time() + timeout
        while time.time() < end:
            if marker in self.buf:
                idx = self.buf.index(marker)
                frame = self.buf[:idx]
                self.buf = self.buf[idx + len(marker):]
                board = extract_board(frame)
                if board is not None:
                    return board
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.2)
            if not ready:
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                return None
            self.buf += chunk
            self.transcript += chunk
        return None

    def send(self, chars: str):
        self.proc.stdin.write(chars.encode("latin1"))
        self.proc.stdin.flush()


def parse_schedule(spec: str):
    if not spec:
        return {}
    out = {}
    for part in spec.split(","):
        frame_s, burst_s = part.split(":", 1)
        burst = []
        for item in burst_s.split("+"):
            item = item.strip()
            if not item:
                continue
            if item.startswith("0x"):
                burst.append(bytes([int(item, 16)]).decode("latin1"))
            else:
                burst.append(item)
        out[int(frame_s)] = "".join(burst)
    return out


def run_probe(game_factory, burst: str, burst_frame: int, frames: int, schedule: str):
    sends = parse_schedule(schedule)
    if burst:
        sends.setdefault(burst_frame, burst)
    with game_factory() as game:
        board = game.next_frame()
        print(f"frame=1 pos={find_player(board)}")
        if 1 in sends:
            game.send(sends[1])
        for frame in range(2, frames + 1):
            board = game.next_frame()
            print(f"frame={frame} pos={find_player(board)}")
            if board is None:
                break
            if frame in sends:
                game.send(sends[frame])
        text = strip_ansi(game.transcript)
        flag = FLAG_RE.search(text)
        if flag:
            print(f"FLAG {flag.group(0)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("pty", "pipe", "remote"), default="pty")
    ap.add_argument("--burst", default="")
    ap.add_argument("--burst-frame", type=int, default=1)
    ap.add_argument("--schedule", default="")
    ap.add_argument("--frames", type=int, default=10)
    ap.add_argument("--container", default="acid_runner")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--host", default="streams.tamuctf.com")
    ap.add_argument("--port", type=int, default=443)
    ap.add_argument("--sni", default="acidity")
    args = ap.parse_args()
    if args.mode == "pty":
        run_probe(lambda: PtyGame(container=args.container), args.burst, args.burst_frame, args.frames, args.schedule)
    elif args.mode == "pipe":
        run_probe(lambda: PipeGame(Path(args.root)), args.burst, args.burst_frame, args.frames, args.schedule)
    else:
        run_probe(lambda: RemoteGame(args.host, args.port, args.sni), args.burst, args.burst_frame, args.frames, args.schedule)


if __name__ == "__main__":
    main()
