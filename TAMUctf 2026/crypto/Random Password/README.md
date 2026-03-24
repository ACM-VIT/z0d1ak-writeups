# Random Password

| Field      | Value |
|------------|-------|
| Category   | crypto |
| Points     | 50 |
| Solves     | 393 |

## Description

<p>Author: <code>Marfung37</code></p><p>Password verification by sleepy counting</p>

## Files

- random-password.tar.gz

## Writeup

### Flag

~~~text
gigem{h3rd1ng_rand0m_sh3ep_LiNBpqRTk}
~~~

### Executive Summary

This challenge looks like a password brute-force problem, but it is actually a deterministic PRNG state-alignment problem.

The verifier seeds Python’s Mersenne Twister with a fixed seed and then, for each bit of your 256-bit password, consumes a variable number of random values:
1. Bit 0: keep summing random numbers until the sum reaches at least 5.
2. Bit 1: keep summing random numbers until the sum reaches at least 17.

After processing all 256 bits, the next random value must equal a fixed constant. Because the seed and logic are fully known, we can reverse this by searching for a bit sequence that lands exactly on the target RNG index. That gives one valid 64-hex password, which returns the flag.

### Vulnerability Analysis

The core issue is deterministic randomness used as a secret validator.

1. Fixed seed: the code calls `random.seed(121728)`, so the random stream is fully predictable.
2. Deterministic transition system: each password bit maps current RNG index to a next index (via threshold-5 or threshold-17 loops).
3. Single-value check: success is `random.random() == 0.9992610559813815` after 256 transitions.
4. No cryptographic hardness: this is not a hash or MAC; it is a path-finding problem over known PRNG outputs.

So instead of guessing password strings, we recover any 256-bit path that causes the final RNG draw to match the constant.

### Exploit Strategy

Model the verifier as a graph search over RNG indices.

1. Precompute a long list of random values from seed 121728.
2. Define transition `T0(i)`:
   sum values starting at index `i` until sum >= 5, return new index.
3. Define transition `T1(i)`:
   sum values starting at index `i` until sum >= 17, return new index.
4. Run DP/BFS for 256 steps:
   keep reachable indices and predecessor info `(prev_index, bit)`.
5. Among indices reachable at depth 256, find one where `vals[index]` equals target `0.9992610559813815`.
6. Backtrack predecessors to recover 256-bit password, convert to 64-char hex.

Recovered valid password:
~~~text
00000000000000000000000000000000ffffffffefffffffffffffffffffff7f
~~~

### Implementation

Solver script:

~~~python
import random

TARGET = 0.9992610559813815
BITS = 256

def step(vals, i, threshold):
    s = 0.0
    while s < threshold:
        s += vals[i]
        i += 1
    return i

# Generate enough MT outputs from known seed
N = 60000
r = random.Random(121728)
vals = [r.random() for _ in range(N)]

# Memoized transitions from any RNG index
next0 = {}
next1 = {}

def go0(i):
    if i not in next0:
        next0[i] = step(vals, i, 5)
    return next0[i]

def go1(i):
    if i not in next1:
        next1[i] = step(vals, i, 17)
    return next1[i]

# layers[t]: reachable indices after t bits
# store predecessor in next layer as (prev_index, bit_char)
layers = [dict() for _ in range(BITS + 1)]
layers[0][0] = None

for t in range(BITS):
    nxt = layers[t + 1]
    for i in layers[t].keys():
        j0 = go0(i)
        if j0 not in nxt:
            nxt[j0] = (i, "0")
        j1 = go1(i)
        if j1 not in nxt:
            nxt[j1] = (i, "1")

accept = [i for i in layers[BITS].keys() if vals[i] == TARGET]
if not accept:
    raise SystemExit("No solution found")

# Reconstruct one valid bitstring
i = accept[0]
bits = []
for t in range(BITS, 0, -1):
    prev, b = layers[t][i]
    bits.append(b)
    i = prev
bits = "".join(reversed(bits))

password_hex = hex(int(bits, 2))[2:].zfill(64)
print(password_hex)
~~~

Optional remote check using pwntools:

~~~python
from pwn import remote

pw = "00000000000000000000000000000000ffffffffefffffffffffffffffffff7f"
io = remote("streams.tamuctf.com", 443, ssl=True, sni="random-password")
io.recvuntil(b"Enter the password in hex: ")
io.sendline(pw.encode())
print(io.recvall(timeout=2).decode(errors="ignore"))
~~~

### Execution & Results

1. Ran the DP solver to recover a valid 64-hex password.
2. Submitted password to service.
3. Service returned:

~~~text
Here's the flag gigem{h3rd1ng_rand0m_sh3ep_LiNBpqRTk}
~~~

The challenge is solved by PRNG-state path recovery, not brute-force guessing.
