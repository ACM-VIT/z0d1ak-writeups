# compute it

| Field      | Value |
|------------|-------|
| Category   | Reverse Engineering |
| Points     | 141 |
| Solves     | 135 |

## Description

the computation prof gave me some data and a executable , what does he want from me?

author - martin

## Files

- [signal_data.txt](./signal_data.txt)
- [validator](./validator)

## Writeup

### Flag

```text
EH4X{N3WT0N-W4S-R1GHT}
```

### Executive Summary

`validator` checks whether a complex starting point converges to a specific root of `z^3 - 1` in exactly 12 Newton iterations. Running this same check over all 2600 `(real, imag)` pairs in `signal_data.txt` produces a bitstream that renders a pixel message containing the flag.

### Vulnerability Analysis

Disassembly shows the binary does not compare against hidden strings directly. Instead it computes iterative numeric behavior:

- Input: two floating-point values (`x`, `y`).
- Iteration cap: `0x31` (50 loops).
- Newton update for complex polynomial `f(z)=z^3-1`.
- Accept condition: iteration count equals exactly `12`.

Recovered constants (`.rodata`):

- `3.0`, `1.0`, `6.0`
- denominator guard `1e-9`
- convergence tolerance `1e-6`

### Exploit Strategy

1. Reimplement validator math exactly.
2. For each row in `signal_data.txt`:
   - output bit `1` if steps == 12, else `0`.
3. Reshape bitstream into a 2D grid (`130 x 20`).
4. Render as pixels (`#`/`.`) and read text band from middle rows.

### Implementation

Core equations per step:

- `fr = x^3 - 3xy^2 - 1`
- `fi = 3x^2y - y^3`
- `j11 = 3(x^2 - y^2)`
- `j12 = 6xy`
- `den = j11^2 + j12^2`
- `dx = (fr*j11 + fi*j12)/den`
- `dy = (fi*j11 - fr*j12)/den`
- update `(x, y) = (x-dx, y-dy)`

Accept exactly when iteration counter equals 12.

### Execution & Results

Applying the classifier to all 2600 points produced a clean embedded message, resolving to the final flag.

