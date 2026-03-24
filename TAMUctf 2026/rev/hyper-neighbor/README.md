# hyper-neighbor

| Field      | Value |
|------------|-------|
| Category   | rev |
| Points     | 73 |
| Solves     | 121 |

## Description

<p>Author: <code>addison</code></p><p>Somewhere, somehow, a neighbor is running the attached binary with the following command:</p><pre><code>hyper-neighbor flag.txt /lib/libc.musl-x86_64.so.1</code></pre><p>I have no idea what it's doing, or how we can try to read the flag. Give it a go?</p>

## Files

- [hyper-neighbor.tar.gz](./hyper-neighbor.tar.gz)

## Writeup

### Flag

```text
gigem{you-really-need-to-calm-down-10aa082660957ffe}
```

### Executive Summary

This challenge is a cross-process cache side channel, not a memory corruption bug. The `hyper-neighbor` binary repeatedly encodes `flag.txt` into cache state by `clflush`ing specific cache-line offsets of a shared mapped file (`/lib/libc.musl-x86_64.so.1`).

Because both processes map the same file-backed pages, a second process can recover those encoded bits using reload timing (Flush+Reload style). After collecting many noisy 64-bit samples and majority-voting by embedded chunk counter, we reconstruct the full flag reliably.

### Vulnerability Analysis

Initial triage of the binary:

- ELF64, static PIE, Rust symbols preserved
- `send::main` symbol present
- Panic path references `bin/send.rs`
- Running without args panics with `Need a file to send!`

From reversing `send::main`, the behavior is:

1. Read argument 1 (`flag.txt`) and load file bytes.
2. Read argument 2 (shared library path).
3. Open and `mmap` argument 2 with shared, read-only mapping.
4. Compute a cache-line stride from CPUID-derived cache geometry.
5. Repeatedly emit framed 64-bit words by flushing selected lines.

Frame markers:

- start: `0xdeadbeef00000001`
- end: `0xdeadbeef00000002`

Payload word construction for each 4-byte chunk:

```c
chunk = little_endian_u32(data[i:i+4]);  // zero-padded final chunk
ctr   = i;                                // 16-bit chunk index

c1 = crc32_u32(0, chunk);
c2 = crc32_u16(c1, ctr);
hi16 = (c2 ^ (c2 >> 16)) & 0xffff;

word = chunk | ((uint64_t)ctr << 32) | ((uint64_t)hi16 << 48);
```

For each `word`, bits `0..63` are sent by conditionally flushing line `base + bit*stride` when that bit is `1`.

Why this leaks cross-process: file-backed pages of `/lib/libc.musl-x86_64.so.1` are physically shared via the page cache. Victim flushes and attacker reload timings become a covert channel.

### Exploit Strategy

High-level solve flow:

1. Connect to remote service and solve proof-of-work.
2. Use spawned shell (`/bin/ash`).
3. Run timing probe on another core.
4. For each sample window, time 64 candidate lines and infer one noisy 64-bit word.
5. Collect many samples.
6. Parse `ctr = (word >> 32) & 0xffff`, group words by `ctr`, and majority-vote `chunk = word & 0xffffffff`.
7. Reassemble chunks in counter order to recover bytes.

Remote constraints encountered:

- No Python in jail shell.
- No compiler in jail shell.

Adaptation:

- Build static probe locally.
- Upload probe as base64 to `/tmp`.
- Execute remotely, save raw output.
- Decode output locally.

### Implementation

Representative local build:

```bash
gcc -O2 -static probe.c -o probe_static
```

Representative remote capture:

```sh
taskset -c 1 /tmp/probe 20 120 120000 /lib/libc.musl-x86_64.so.1 > /tmp/o.txt
```

Core probe logic (simplified):

```c
for (int sample = 0; sample < samples; sample++) {
  uint64_t bits = 0;

  for (int r = 0; r < rounds; r++) {
    shuffle(order, 64);
    for (int j = 0; j < 64; j++) {
      int i = order[j];
      t = reload_timing(base + i * stride);
      if (t > threshold) votes[i]++;
    }
  }

  for (int i = 0; i < 64; i++) {
    if (votes[i] > rounds / 2) bits |= (1ULL << i);
  }
  printf("%016llx\n", (unsigned long long)bits);
}
```

Decoder sketch used locally:

```python
from collections import Counter, defaultdict

by_ctr = defaultdict(list)
for w in words:
  if w == 0:
    continue
  ctr = (w >> 32) & 0xffff
  chunk = w & 0xffffffff
  by_ctr[ctr].append(chunk)

out = bytearray()
for ctr in sorted(by_ctr):
  chunk, _ = Counter(by_ctr[ctr]).most_common(1)[0]
  out += chunk.to_bytes(4, "little")

print(out)
```

### Execution & Results

After long capture and majority decoding, reconstructed plaintext contained:

```text
gigem{you-really-need-to-calm-down-10aa082660957ffe}
```

Key takeaways:

- This challenge demonstrates cache-state exfiltration between processes.
- The shared mapped libc path is the communication substrate.
- `deadbeef...01/02` markers provide robust framing.
- The embedded 16-bit counter makes ordering and recovery straightforward once enough samples are collected.
