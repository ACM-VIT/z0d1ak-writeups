# Hidden Log Factoring

| Field      | Value |
|------------|-------|
| Category   | crypto |
| Points     | 50 |
| Solves     | 429 |

## Description

<p>Author: <code>Marfung37</code></p><p>Where are the logs? I got the raw data in <code>data.txt</code> but can't find the logs.</p>

## Files

- [hidden-log-factoring.tar.gz](./hidden-log-factoring.tar.gz)

## Writeup

### Flag

```text
gigem{100lsb_ed_fact0ring_rab1n_attack_1n_th3_log_3oVAjvoCTGmWg847g9zsNBIyPPWqYdP}
```

### Executive Summary

The challenge data exposed RSA public values, DLP public values, and two encrypted integers (`D`, `c`).

The core weakness was that the DLP secret exponent `s` was generated with only about 100 bits:

- `s = randint(1, 1 << 100)`

From there, the solve path was:

1. Recover `s` from `A = g^s mod p` using a reduced-order discrete-log strategy.
2. Rebuild the HKDF mask and unmask RSA private exponent `d` from `D = d XOR mask`.
3. Use `(n, e, d)` to recover RSA factors.
4. Decrypt Rabin-style ciphertext `c = m^2 mod n` by square-rooting modulo both primes and CRT-recombining candidates.
5. Select the root containing `gigem{...}`.

### Vulnerability Analysis

The generator combined two systems:

- RSA key generation for `(n, e, d)`
- DLP over prime field `(p, g, A)` with `A = g^s mod p`

It then masked `d` with HKDF keyed by `s`:

- `mask = HKDF(long_to_bytes(s), info="rsa-d-mask")`
- `D = d XOR bytes_to_long(mask)`

Two issues made this breakable:

1. **Small DLP exponent**
   - `s` is bounded by `2^100`, so solving DLP only needs enough subgroup information to recover a 100-bit value.

2. **Masking `d` with recoverable `s`**
   - Once `s` is found, the mask and `d` are immediately recoverable.
   - With valid `d`, RSA factors can be recovered efficiently from `k = ed - 1`.

`c` was encrypted as `m^2 mod n` (Rabin-style), so decryption yields four roots. Only one root decodes to a valid flag string.

### Exploit Strategy

1. Factor `p - 1` to get smooth factors usable by Pohlig-Hellman.
2. Solve DLP in each small-order subgroup and combine residues using CRT.
3. Use recovered `s` to derive HKDF mask and unmask candidate `d`.
4. Validate `d` by recovering factors from `ed - 1` and checking `p*q = n`.
5. Compute square roots of `c` modulo each prime.
6. Recombine the four roots with CRT.
7. Convert each root to bytes and pick the one containing `gigem{`.

### Implementation

I used a Python solver with these main components:

- `factor_p1.py` to inspect and factor `p - 1`
- `solve_full.py` for full exploitation pipeline

Script used to factor `p - 1`:

```python
from sympy import factorint

p = 200167626629249973590210748210664315551571227173732968065685194568612605520816305417784745648399324178485097581867501503778073506528170960879344249321872139638179291829086442429009723480288604047975360660822750743411854623254328369265079475034447044479229192540942687284442586906047953374527204596869578972378578818243592790149118451253249
n = p - 1

print("bitlen p-1", n.bit_length())
fac = factorint(n, limit=10**7)
print("factors found:", fac)
known = 1
for k, v in fac.items():
   known *= k ** v
print("known bits", known.bit_length())
rem = n // known
print("remaining bits", rem.bit_length())
print("remaining", rem)
```

Full exploit script:

```python
from math import gcd, isqrt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def long_to_bytes(x: int) -> bytes:
   if x == 0:
      return b"\x00"
   return x.to_bytes((x.bit_length() + 7) // 8, "big")


# Public values from data.txt
n = 71016310005824589926747341243598522145452505235842335510488353587223142066921470760443852767377534776713566052988373656012584808377496091765373981120165220471527586994259252074709653090148780742972203779666231432769553199154214563039426087870098774883375566546770723222752131892953195949848583409407713489831
e = 65537
p = 200167626629249973590210748210664315551571227173732968065685194568612605520816305417784745648399324178485097581867501503778073506528170960879344249321872139638179291829086442429009723480288604047975360660822750743411854623254328369265079475034447044479229192540942687284442586906047953374527204596869578972378578818243592790149118451253249
g = 11
A = 44209577951808382329528773174800640982676772266062718570752782238450958062000992024007390942331777802579750741643234627722057238001117859851305258592175283446986950906322475842276682130684406699583969531658154117541036033175624316123630171940523312498410797292015306505441358652764718889371372744612329404629522344917215516711582956706994
D = 9478993126102369804166465392238441359765254122557022102787395039760473484373917895152043164556897759129379257347258713397227019255397523784552330568551257950882564054224108445256766524125007082113207841784651721510041313068567959041923601780557243220011462176445589034556139643023098611601440872439110251624
c = 1479919887254219636530919475050983663848182436330538045427636138917562865693442211774911655964940989306960131568709021476461747472930022641984797332621318327273825157712858569934666380955735263664889604798016194035704361047493027641699022507373990773216443687431071760958198437503246519811635672063448591496


def hkdf_mask(secret: bytes, length: int) -> bytes:
   hkdf = HKDF(
      algorithm=hashes.SHA256(),
      length=length,
      salt=None,
      info=b"rsa-d-mask",
      backend=default_backend(),
   )
   return hkdf.derive(secret)


def crt_pair(a1: int, m1: int, a2: int, m2: int):
   inv = pow(m1, -1, m2)
   t = ((a2 - a1) * inv) % m2
   x = a1 + m1 * t
   return x % (m1 * m2), m1 * m2


def bsgs(base: int, target: int, mod: int, order: int) -> int:
   m = isqrt(order) + 1
   table = {}
   cur = 1
   for j in range(m):
      if cur not in table:
         table[cur] = j
      cur = (cur * base) % mod

   factor = pow(pow(base, -1, mod), m, mod)
   gamma = target
   for i in range(m + 1):
      if gamma in table:
         x = i * m + table[gamma]
         if x < order and pow(base, x, mod) == target:
            return x
      gamma = (gamma * factor) % mod

   raise ValueError("dlog not found")


def dlog_mod_2power(base: int, target: int, mod: int, e2: int) -> int:
   x = 0
   for k in range(e2):
      t = (target * pow(base, -x, mod)) % mod
      t = pow(t, 1 << (e2 - 1 - k), mod)
      bit = 0 if t == 1 else 1
      x += bit << k
   return x


print("Recovering s with manual Pohlig-Hellman...")

factors = [(2, 101), (3, 1), (29, 1), (317, 1), (593, 1), (480661, 1)]
x_acc = 0
m_acc = 1

for q, e_q in factors:
   qe = q ** e_q
   h = (p - 1) // qe
   g_sub = pow(g, h, p)
   A_sub = pow(A, h, p)

   if q == 2:
      x_q = dlog_mod_2power(g_sub, A_sub, p, e_q)
   else:
      x_q = bsgs(g_sub, A_sub, p, qe)

   x_acc, m_acc = crt_pair(x_acc, m_acc, x_q, qe)

s = x_acc
print("Recovered s:", s)
print("s bitlength:", s.bit_length())
if s >= (1 << 100):
   raise ValueError("Recovered exponent is out of expected range")

secret = long_to_bytes(s)


def factor_from_d(n_val: int, e_val: int, d_val: int):
   k = e_val * d_val - 1
   t = k
   r = 0
   while t % 2 == 0:
      t //= 2
      r += 1

   for a in range(2, 200):
      x = pow(a, t, n_val)
      if x in (1, n_val - 1):
         continue
      for _ in range(r):
         y = pow(x, 2, n_val)
         if y == 1:
            p_fac = gcd(x - 1, n_val)
            if 1 < p_fac < n_val:
               return p_fac, n_val // p_fac
            break
         x = y
         if x == n_val - 1:
            break
   return None


def tonelli_shanks(a: int, prime: int) -> int:
   if a == 0:
      return 0
   if pow(a, (prime - 1) // 2, prime) != 1:
      raise ValueError("not a square modulo prime")
   if prime % 4 == 3:
      return pow(a, (prime + 1) // 4, prime)

   q = prime - 1
   s_pow = 0
   while q % 2 == 0:
      q //= 2
      s_pow += 1

   z = 2
   while pow(z, (prime - 1) // 2, prime) != prime - 1:
      z += 1

   m = s_pow
   c_val = pow(z, q, prime)
   t_val = pow(a, q, prime)
   r_val = pow(a, (q + 1) // 2, prime)

   while t_val != 1:
      i = 1
      temp = pow(t_val, 2, prime)
      while temp != 1:
         temp = pow(temp, 2, prime)
         i += 1
      b = pow(c_val, 1 << (m - i - 1), prime)
      m = i
      c_val = (b * b) % prime
      t_val = (t_val * c_val) % prime
      r_val = (r_val * b) % prime

   return r_val


for mask_len in (127, 128):
   mask = hkdf_mask(secret, mask_len)
   d = D ^ int.from_bytes(mask, "big")
   fac = factor_from_d(n, e, d)
   if not fac:
      continue

   p1, q1 = fac
   if p1 * q1 != n:
      continue

   print("Recovered RSA factors.")

   rp = tonelli_shanks(c % p1, p1)
   rq = tonelli_shanks(c % q1, q1)

   inv_q_mod_p = pow(q1, -1, p1)
   inv_p_mod_q = pow(p1, -1, q1)

   roots = []
   for sp in (rp, (-rp) % p1):
      for sq in (rq, (-rq) % q1):
         root = (sp * q1 * inv_q_mod_p + sq * p1 * inv_p_mod_q) % n
         roots.append(root)

   for m in roots:
      msg = long_to_bytes(m)
      if b"gigem{" in msg:
         print("FLAG:", msg.decode(errors="ignore"))
         raise SystemExit

print("Flag not found")
```

Important implementation details:

1. `p - 1` factored as:
   - `2^101 * 3 * 29 * 317 * 593 * 480661 * large_prime`
2. Smooth-part modulus exceeded the secret range, so `s mod M` uniquely gave `s`.
3. Manual Pohlig-Hellman was implemented to avoid slow/buggy generic `discrete_log` behavior.
4. `d` recovery tested both likely HKDF lengths (`127`, `128`) due to integer-byte-length edge behavior.
5. Factoring from `(n, e, d)` used the standard `k = ed - 1` decomposition and nontrivial gcd extraction.
6. Rabin decryption used Tonelli-Shanks per prime and CRT recombination to enumerate all four roots.

Core command used:

```bash
python3 solve_full.py
```

### Execution & Results

Observed successful run output:

```text
Recovering s with manual Pohlig-Hellman...
Recovered s: 485391067385099231898174017598
s bitlength: 99
Recovered RSA factors.
FLAG: gigem{100lsb_ed_fact0ring_rab1n_attack_1n_th3_log_3oVAjvoCTGmWg847g9zsNBIyPPWqYdP}
```

Exact one-line flag verification was done with:

```bash
python3 solve_full.py | sed -n 's/^FLAG: //p' | cat -A
```

Which confirmed:

```text
gigem{100lsb_ed_fact0ring_rab1n_attack_1n_th3_log_3oVAjvoCTGmWg847g9zsNBIyPPWqYdP}
```
