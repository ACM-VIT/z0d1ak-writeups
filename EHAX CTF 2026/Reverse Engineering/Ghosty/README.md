# Ghosty

| Field      | Value |
|------------|-------|
| Category   | Reverse Engineering |
| Points     | 254 |
| Solves     | 112 |

## Description

How freaky can you get with the ghost?

nc chall.ehax.in 22222

Handout: https://cdn.ehax.in/handout_ghosty.zip

`Author: nrg & the_moon_guy`

## Writeup

### Flag

```text
EH4X{fr3k7_fri3n5dly_1nt3rf4c35_0nc3_4g41n}
```

### Executive Summary

`main.lua` only builds callback APIs and forwards input to `libruntime.so`. The real checker is a stage-2 shared object decrypted and loaded in memory at runtime. Dumping that second-stage ELF and analyzing its `pulse` function reveals the expected input token directly.

### Vulnerability Analysis

The security model relies on runtime-only code loading:

- Stage 1 (`libruntime.so`) decrypts an embedded payload and loads it with `memfd` + `dlopen`.
- Stage 2 implements the actual verification logic.
- Because stage 2 is written to memory through regular `write()` calls, it can be captured with `LD_PRELOAD` instrumentation.

So the challenge is not cryptographically hard; it is a staged unpacking/reversing task.

### Exploit Strategy

1. Review `main.lua` to confirm callbacks and entry flow.
2. Reverse `libruntime.so` to identify in-memory ELF loading behavior.
3. Hook `write()` using `LD_PRELOAD` and dump the memfd payload when ELF bytes appear.
4. Load dumped `stage2_dump.so`, locate exported dispatch (`catalog`) and checker (`pulse`).
5. Observe runtime state near the final comparison in `pulse` to extract the expected token.

Recovered token:

```text
ghost_8d3f4a91c2e7b6d0
```

### Implementation

Practical workflow:

- Build a minimal `write()` hook that:
  - Detects first buffer starting with `\x7fELF`.
  - Tracks that FD.
  - Mirrors all later writes on that FD to `stage2_dump.so`.
- Execute local harness invoking `entry(api, inp, 32)`.
- Inspect dumped stage-2 in GDB at a post-transform point in `pulse` (for example near `pulse+0x238`).
- Read expected cleartext bytes from stack memory.

### Execution & Results

Submitting the plaintext token to the remote service returns the flag:

```bash
printf 'ghost_8d3f4a91c2e7b6d0\n' | nc chall.ehax.in 22222
```

