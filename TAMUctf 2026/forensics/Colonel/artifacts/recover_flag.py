#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


HEX_CANDIDATE_1 = "51782b4b765251314e32525236364978534d35566a6b72474b67303946483266"
HEX_CANDIDATE_2 = "58782b4b765251314e51525235364978534d35566a6a72524b673039466c3265"
BAD_1 = {9, 21, 31}
BAD_2 = {0, 12, 23, 29}
IV = "1234567890123456"


def reconstruct_key() -> str:
    k1 = bytes.fromhex(HEX_CANDIDATE_1).decode()
    k2 = bytes.fromhex(HEX_CANDIDATE_2).decode()

    merged: list[str] = []
    for i, (a, b) in enumerate(zip(k1, k2)):
        if i in BAD_1:
            merged.append(b)
        elif i in BAD_2:
            merged.append(a)
        else:
            if a != b:
                raise ValueError(f"Unexpected mismatch at index {i}: {a!r} vs {b!r}")
            merged.append(a)
    return "".join(merged)


def decrypt_flag(ciphertext: Path) -> bytes:
    key = reconstruct_key()
    proc = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-K",
            key.encode().hex(),
            "-iv",
            IV.encode().hex(),
            "-nopad",
            "-in",
            str(ciphertext),
        ],
        check=True,
        capture_output=True,
    )
    return proc.stdout.rstrip(b"\x00")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct the Colonel AES key from leaked kmsg candidates and decrypt flag.enc."
    )
    parser.add_argument("flag_enc", type=Path, help="Path to flag.enc")
    args = parser.parse_args()

    key = reconstruct_key()
    plaintext = decrypt_flag(args.flag_enc)

    print(f"Recovered key: {key}")
    print(f"IV: {IV}")
    print(f"Plaintext: {plaintext.decode()}")


if __name__ == "__main__":
    main()
