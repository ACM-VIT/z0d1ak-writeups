# #808080

| Field      | Value |
|------------|-------|
| Category   | Miscellaneous |
| Points     | 263 |
| Solves     | 110 |

## Description

`authro: seyya`

gray code ? nah grey code

```0010111100011010000101111111110110010010000100010111011001000110010000011111101101100111010000010101011001111110010000000111010001111110010000011```

http://chall.ehax.in:8076/

> Note: flag format for this challenge is CTF{...}

## Writeup

### Flag

```text
CTF{GREY&CODE#GOES_VERY_H@RD}
```

### Executive Summary

The backend validates a 32-element, 5-bit wheel. Error messages disclose that valid wheels must be unique and adjacent values must differ by exactly one bit, which is exactly a 5-bit Gray code cycle. Once this is identified, only orientation and rotation remain unknown (64 candidates total).

### Vulnerability Analysis

The challenge leaks structural rules through `/api/validate-wheel` responses:

- Duplicate values are explicitly rejected.
- Adjacent Hamming distance is explicitly reported and must be exactly 1.
- Wheel length must be 32.

These diagnostics expose the hidden constraint system and reduce the search space to deterministic brute force.

### Exploit Strategy

1. Generate canonical 5-bit Gray code:

```python
[format(i ^ (i >> 1), '05b') for i in range(32)]
```

2. Enumerate:
   - forward/reverse orientation (2 choices),
   - all cyclic rotations (32 choices).
3. Send each wheel to `/api/decode` with the provided binary input.
4. Stop when decoded output contains `CTF{...}`.

### Implementation

Reference solver logic:

```python
import requests

BASE = "http://chall.ehax.in:8076"
BINARY = "0010111100011010000101111111110110010010000100010111011001000110010000011111101101100111010000010101011001111110010000000111010001111110010000011"

gray = [format(i ^ (i >> 1), "05b") for i in range(32)]

for rev in [False, True]:
    seq = gray[::-1] if rev else gray
    for rot in range(32):
        wheel = seq[rot:] + seq[:rot]
        r = requests.post(
            f"{BASE}/api/decode",
            json={"binaryInput": BINARY, "wheelData": wheel},
            timeout=10,
        )
        decoded = r.json().get("decoded", "")
        if "CTF{" in decoded:
            print(rev, rot, decoded)
            raise SystemExit
```

### Execution & Results

The valid candidate was the forward Gray sequence with a rotation offset of `4`, which decoded to the final flag.

