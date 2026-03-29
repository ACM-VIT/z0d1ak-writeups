# i guess bro

| Field      | Value |
|------------|-------|
| Category   | Reverse Engineering |
| Points     | 50 |
| Solves     | 354 |

## Description

`author: benzo`

meh yet another crackme challenge

## Files

- [chall](./chall)

## Writeup

### Flag

```text
EH4X{y0u_gu3ss3d_th4t_r1sc_cr4ckm3}
```

### Executive Summary

`chall` is a stripped, statically linked RISC-V ELF crackme. The binary enforces prefix/suffix/length checks, a global byte-sum check, and a compact arithmetic check over selected indices. The full flag can be recovered directly from an encoded `.rodata` blob used by the validator.

### Vulnerability Analysis

Key observations from disassembly:

- Decoy flag-like strings are present in `.rodata` to mislead static string extraction.
- Real validation code verifies:
  - exact length: 35,
  - prefix: `EH4X{`, suffix: `}`,
  - checksum of all bytes equals `0xCAB`,
  - additional arithmetic relation on positions `[5,10,15,20,25,30]`.
- A 35-byte encoded constant is transformed with index-dependent XOR to produce the expected flag text.

### Exploit Strategy

1. Disassemble candidate validation routines (`objdump` around main call graph).
2. Locate encoded 35-byte table in `.rodata`.
3. Reproduce decode transform:
   - `decoded[i] = enc[i] ^ (i*7) ^ 0xA5`
4. Verify decoded string satisfies fixed format and checksum checks.

### Implementation

Tooling used:

- `riscv64-linux-gnu-objdump -d`
- `readelf -x .rodata`
- small script to extract bytes and apply transform

This avoids brute force and yields the exact expected input immediately.

### Execution & Results

Decoded output from the validation table matched:

```text
EH4X{y0u_gu3ss3d_th4t_r1sc_cr4ckm3}
```

