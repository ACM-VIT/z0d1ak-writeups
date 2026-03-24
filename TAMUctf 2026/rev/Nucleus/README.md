# Nucleus

| Field      | Value |
|------------|-------|
| Category   | rev |
| Points     | 50 |
| Solves     | 359 |

## Description

<p>Author: <code>beds</code></p><p>This lab specimen is mysterious... it seems to be evolving. Get to the bottom of it for me, will you?</p>

## Files

- [nucleus.tar.gz](./nucleus.tar.gz)

## Writeup

### Flag

```text
gigem{RCD4Ta_i5_N3aT}
```

### Executive Summary

This challenge is a self-evolving Windows PE executable. Each generation creates the next generation filename (`...21.exe` -> `...22.exe`, etc.), mutates itself, and stores encoded payload data in a PE resource.

The core trick is that each generation writes resource type `RT_RCDATA` (numeric type `10`), resource ID `101`, where the resource content is the previous executable XOR-encoded with a one-byte key.

By repeatedly extracting resource `10/101` and reversing the XOR encoding, we can walk backward through all generations until no further embedded resource exists. The collected XOR keys form the hidden message, and reversing those bytes reveals the flag.

### Vulnerability Analysis

The binary is not vulnerable in a memory-corruption sense; instead, it is logically weak by design:

1. It stores full prior-stage executables in a predictable resource location (`RT_RCDATA`, ID `101`).
2. It protects data using only single-byte XOR.
3. The decoded payload can be validated immediately because PE files begin with `MZ`.
4. The evolution process leaves a deterministic breadcrumb trail across generations.

Static reversing showed:

- `main` copies the executable to a new name and increments the numeric suffix.
- A helper routine reads the source file bytes, XORs every byte with a single input byte, and calls:
  - `BeginUpdateResourceA`
  - `UpdateResourceA` with type `10`, name `101`
  - `EndUpdateResourceW`

### Exploit Strategy

1. Extract `nucleus.tar.gz`.
2. Reverse the executable behavior enough to identify the resource write pattern.
3. Build a decoder that:
   - Reads resource `10/101` from current EXE.
   - Recovers XOR key via `key = blob[0] ^ 0x4d` (`'M'` in `MZ`).
   - Decodes the blob with that key.
   - Saves decoded payload as previous generation executable.
   - Repeats until no matching resource exists.
4. Convert recovered keys to ASCII, then reverse the resulting string.

### Implementation

Unpack and triage:

```bash
tar -xzf nucleus.tar.gz
file nucleus21.exe
rabin2 -i nucleus21.exe
```

Key static-reversing observations (from disassembly):

```text
- CreateFileA / ReadFile reads full executable into memory
- getchar obtains one-byte mutation key
- Buffer is XORed byte-by-byte (SIMD-optimized loop + scalar tail)
- BeginUpdateResourceA(target_exe, FALSE)
- UpdateResourceA(hUpdate, 10, 101, 0, xor_buffer, size)
- EndUpdateResourceW(hUpdate, discardFlag)
```

Automated decoder (core logic):

```python
import pefile
from pathlib import Path


def get_rcdata_10_101(data: bytes):
    pe = pefile.PE(data=data, fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
    )
    for entry in getattr(pe, "DIRECTORY_ENTRY_RESOURCE", []).entries:
        if entry.id == 10:  # RT_RCDATA
            for name_entry in entry.directory.entries:
                if getattr(name_entry, "id", None) == 101:
                    lang_entry = name_entry.directory.entries[0]
                    s = lang_entry.data.struct
                    return pe.get_data(s.OffsetToData, s.Size)
    return None


cur = Path("nucleus21.exe").read_bytes()
keys = []
for depth in range(1, 300):
    blob = get_rcdata_10_101(cur)
    if blob is None:
        break

    key = blob[0] ^ 0x4D  # 'M' from PE magic "MZ"
    assert (blob[1] ^ key) == 0x5A

    cur = bytes(b ^ key for b in blob)
    keys.append(key)
    Path(f"recovered_{depth:03d}.exe").write_bytes(cur)

print(keys)
print(bytes(keys)[::-1].decode())
```

Recovered key bytes:

```text
[125, 84, 97, 51, 78, 95, 53, 105, 95, 97, 84, 52, 68, 67, 82, 123, 109, 101, 103, 105, 103]
```

ASCII of those bytes:

```text
}Ta3N_5i_aT4DCR{megig
```

Reverse the string:

```text
gigem{RCD4Ta_i5_N3aT}
```

### Execution & Results

Run:

```bash
python solve_nucleus.py
```

Observed:

```text
depth=1 key=125 size=289792
...
depth=21 key=103 size=13312
No resource at depth 22
total_depth 21
```

Final decoded flag:

```text
gigem{RCD4Ta_i5_N3aT}
```
