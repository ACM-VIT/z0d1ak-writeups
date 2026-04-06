# Small World

| Field      | Value |
|------------|-------|
| Category   | Cryptography |
| Points     | 50 |
| Solves     | 126 |

## Description

Our intern implemented a "secure" encryption script using a Linear Congruential Generator (LCG). He assured us verbally that LCGs are mathematically sound. We don't believe him so can you recover the seed and decrypt the flag?

Flag Format:
`hackzero{}`

## Files

- [Small_World.zip](./Small_World.zip)

## Writeup

This one is short but very smart. The trap is simple and beautiful.


> ```Flag:```  `hackzero{sm4ll_k3ys_4r3_b4d}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Small World
- **Category:** Cryptography
- **Points:** 50
- **Author:** @AnkitS01
- **Solved By:** ret2.libc

## 1. What I got
I got 3 files:

- `source.py`
- `output.txt` (leaked number)
- `flag.enc` (hex ciphertext)

## 2. Reading the source
The script uses an LCG i.e., which means Linear Congruential Generator.

Formula is, 

`state_{n+1} = (A · state_n + C) mod M`

with:

- `A = 1664525`
- `C = 1013904223`
- `M = 2^32`

Then encryption does:

- one `lcg.next()` stored as leak
- for each flag character: `key_byte = lcg.next() % 256`
- ciphertext byte = plaintext byte XOR key byte

## 3. Weak point
Only `% 256` is used for key bytes.
So only the last 8 bits of LCG output matter.

That means many seeds give the same keystream bytes.
If seeds differ by 256, their low byte is same, so stream is same for this use-case.

Nice design mistake from the intern, and very nice challenge idea from author.

## 4. Recovery approach
I brute-forced seed range `0..1000` (from commented code), decrypted, and checked flag format `hackzero{...}`.

I got:

`hackzero{sm4ll_k3ys_4r3_b4d}`

Valid equivalent seeds in `0..1000`:

- `196`
- `452`
- `708`
- `964`

(all differ by 256)

## 5. Python solve script (what I ran to get the flag)
```python
A = 1664525
C = 1013904223
M = 2**32

ct = bytes.fromhex("fe9c5b5c50e49e3485368d8b7e254b0855f4fb18ce630f34ace154b2")

def dec(seed):
    s = seed
    s = (A*s + C) % M  # first call used as leak in challenge code
    out = []
    for b in ct:
        s = (A*s + C) % M
        k = s % 256
        out.append(b ^ k)
    return bytes(out)

for seed in range(1001):
    pt = dec(seed)
    if pt.startswith(b"hackzero{") and pt.endswith(b"}"):
        print(seed, pt.decode())
```

## 6. Trials
Tried with cyberchef was facing few unknow bytes, ? inbetween flags, used ai, (prompted what is needed and what should be done and what that python code should do), rest recon were from pure brain 👀.

## Author

ret2.libc
