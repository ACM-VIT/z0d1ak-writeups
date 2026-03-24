# Quick Response

| Field      | Value |
|------------|-------|
| Category   | misc |
| Points     | 50 |
| Solves     | 345 |

## Description

<p>Author: <code>faefeyfa</code></p><p>If you're bored, check this one out!</p>

## Files

- [quick-response.tar.gz](./quick-response.tar.gz)

## Writeup

### Flag

```text
gigem{d1d_y0u_n0t1c3_th3_t1m1n9_b175}
```

### Executive Summary

The challenge provides a tiny PNG wrapped in a tarball and hints at QR behavior via its name: **Quick Response**. Direct QR decoding fails (`zbarimg` returns nothing), so this is not a plain QR image.

The key observation is that the image size is `928 x 928`, and:

- `928 = 29 x 32`

A `29x29` module grid corresponds to a valid QR dimension (Version 3). This reveals that the image is a block-scaled module matrix where each logical module is `32x32` pixels. From there, the solve is to reconstruct the logical matrix, then brute-force a small family of likely visual transformations (mask/inversion/flip/rotation) until a valid QR payload decodes.

### Vulnerability Analysis

This is not a software memory-corruption bug; it is an **obfuscation weakness** in challenge design:

1. The payload remains QR-structured.
2. The transformation space is finite and enumerable.
3. The image dimensions leak exact module geometry.

So the challenge depends on preventing naive decoders, but it can still be defeated by systematic reconstruction and search.

Technical indicators:

- Normal QR decoder fails on original image.
- No obvious metadata flag in EXIF/text chunks.
- Run-length periodicity clearly indicates fixed-size module scaling.
- Candidate transformed matrices decode cleanly once the correct mapping is applied.

### Exploit Strategy

Use a deterministic pipeline:

1. Unpack and triage the file.
2. Confirm dimensions and infer module size.
3. Convert image into a `29x29` logical bit matrix (dark/light per `32x32` block).
4. Enumerate realistic transformations:
   - rotations: 0/90/180/270
   - flips: horizontal/vertical toggles
   - inversion toggle
   - checker/periodic/QR-like masks with phase shifts
5. Render each candidate with adequate quiet zone.
6. Decode each candidate with `zbarimg`.
7. Stop on first valid QR result.

This avoids guesswork and is robust to most QR-style visual obfuscations.

### Implementation

Initial triage:

```bash
tar -xzf quick-response.tar.gz
file quick-response.png
exiftool quick-response.png
zbarimg -q quick-response.png
```

Dimension clue:

```bash
python3 - << 'PY'
w = h = 928
print(w // 32, h // 32)
PY
```

Output:

```text
29 29
```

Core extraction idea (module reduction):

```python
# For each 32x32 block, classify as dark/light by average intensity.
base = [[0] * 29 for _ in range(29)]
for y in range(29):
    for x in range(29):
        s = 0
        for yy in range(y * 32, (y + 1) * 32):
            for xx in range(x * 32, (x + 1) * 32):
                r, g, b = px[xx, yy]
                s += (r + g + b)
        base[y][x] = 1 if s < (32 * 32 * 3 * 128) else 0
```

Transformation brute-force loop (excerpt):

```python
for r in range(4):
    m0 = rot(base, r)
    for fh in [0, 1]:
        m1 = flip_h(m0) if fh else m0
        for fv in [0, 1]:
            m2 = flip_v(m1) if fv else m1
            for name, fn in mask_fns.items():
                for sx in range(3):
                    for sy in range(3):
                        for inv in [0, 1]:
                            candidate = transform(m2, fn, sx, sy, inv)
                            write_candidate_png(candidate)
                            out = decode_with_zbarimg()
                            if out:
                                print(out)
                                raise SystemExit(0)
```

Actual solver used in this directory:

- `bruteforce_qr.py`

### Execution & Results

Run the solver:

```bash
python3 bruteforce_qr.py
```

Successful decode:

```text
bf_qr/cand_00002_checker_r0_fh0_fv0_sx0_sy0_inv0.png => QR-Code:gigem{d1d_y0u_n0t1c3_th3_t1m1n9_b175}
```

Final flag:

```text
gigem{d1d_y0u_n0t1c3_th3_t1m1n9_b175}
```
