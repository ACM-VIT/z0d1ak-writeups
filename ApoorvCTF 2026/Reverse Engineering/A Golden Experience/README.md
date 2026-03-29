# A Golden Experience

| Field      | Value |
|------------|-------|
| Category   | Reverse Engineering |
| Points     | 50 |
| Solves     | 381 |

## Description

You have won, the flag is printing and then you hear it, REQUIEM!!!!!!

> Author : shura356

## Files

- [requiem](./requiem)

## Writeup

### Flag

```text
apoorvctf{N0_M0R3_R3QU13M_1N_TH15_3XP3R13NC3}
```

### Executive Summary

The binary is a stripped Rust executable that appears to print progress messages but hides the real flag behind an encoded byte table. Static analysis around the decode routine shows a fixed XOR transformation over 45 bytes. Decoding that region yields the flag directly.

### Vulnerability Analysis

The challenge uses obfuscation rather than runtime entropy:

- User-facing output implies progress but does not expose real flag bytes.
- Actual flag data is stored encoded in the binary's data section.
- Decode loop is deterministic: each byte is XORed with `0x5a`.

Once the encoded offset and length are identified, recovery is straightforward.

### Exploit Strategy

1. Trace execution near printed status strings.
2. Identify decode loop and constants:
   - buffer length: `0x2d` bytes,
   - transform: `decoded[i] = encoded[i] ^ 0x5a`.
3. Extract encoded byte blob from file.
4. Apply XOR transform to recover plaintext flag.

### Implementation

Minimal extraction flow:

```python
from pathlib import Path

b = Path("requiem").read_bytes()
o = 0x484f4
n = 0x2d
enc = b[o:o+n]
print(bytes(x ^ 0x5a for x in enc).decode())
```

### Execution & Results

Decoding the 45-byte encoded sequence prints the final flag shown above.

