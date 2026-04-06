# An Open Secret

| Field      | Value |
|------------|-------|
| Category   | Cryptography |
| Points     | 250 |
| Solves     | 54 |

## Description

Two systems met somewhere on the network. They exchanged numbers, performed their rituals, and left, confident that no one watching could ever reconstruct what they agreed upon. Unfortunately for them, we were watching. A packet capture of their conversation has been recovered. It’s messy. There’s noise, chatter, and a lot of confidence in how “secure” everything is buried inside, however, is everything you need. **The math looks solid.** The values look large. Nothing obviously broken. **But security isn’t just about choosing the right algorithm it’s about how you use it.** If you think this can be solved with a clever shortcut, think again. You might need to go further than you initially expect. Recover the shared secret and use it to unlock what they tried to hide.

Flag Format:
`hackzero{}`

## Files

- [AnOpenSecret_Crypto.zip](./AnOpenSecret_Crypto.zip)

## Writeup

> ```Flag:```  `hackzero{br41nfuck_is_not_r34l!}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Open Secret
- **Category:** Cryptography
- **Points:** 250
- **Author:** @Snehil(Mr0x00)
- **Solved By:** ret2.libc



Big respect to the challenge author(s). This one is very nice because the math looks strong at first, but the real crack is in how they used it.

## 1) What I got
I got two files from the challenge zip:

- `captured.pcapng` i.e., which means a packet capture file (network traffic dump)
- `flag.txt.gpg` i.e., which means a GPG-encrypted file

## 2) My environment and tools
I solved this in Kali and used:

- `tshark` (CLI Wireshark)
- `python3`
- Python libs: `scapy`, `sympy`, `pgpy`
- `sha256` from Python `hashlib`

Install commands I used:

```bash
sudo apt update
sudo apt install -y tshark python3 python3-pip gnupg
python3 -m pip install --break-system-packages scapy sympy pgpy
```

Tool substitutes that can do same jobs:

- Wireshark GUI instead of `tshark`
- `pyshark`/`dpkt` instead of `scapy`
- `sage` instead of `sympy` for number theory
- `gpg` command line if passphrase is known

## 3) First look at pcap
I quickly checked packet payloads:

```bash
tshark -r captured.pcapng -Y "udp && data" -T fields -e data.text | head
```

I noticed many packets like:

```text
id=1&data=...
id=2&data=...
```

And every 50th packet looked like “secure channel” noise text.

Inside that noise, I found this block repeated:

```text
# Intercepted Key Exchange
p = ...
g = 2
A = ...
B = ...
```

So this is DH, i.e., which means Diffie-Hellman key exchange.

## 4) Extracted DH values
I used these values:

```python
p = 8736489073805684086305179507451312145336960198850222450321684285045258466628525808781552246900007804506276394992600728538533608361706639189532331964901531
g = 2
A = 2794996066442934640383396708993220584783762169186726070188366297468316333265452428474082701535690342706174889597372484008702943319781202470240884210613693
B = 1210454350578824211787039637709213524440747952483190753841197066710749405257527570548081311766060600166395746681022324544415844366753788799012419699450666
```

## 5) Why this breaks
Normally DH is hard because finding private exponent from public key is discrete log problem.

But here private exponents were too small, i.e., which means low-entropy/short random values.

So I ran BSGS, i.e., which means Baby-Step Giant-Step, and recovered:

```text
a = 225118447
b = 234797908
```

Then shared secret:

```text
S = 2917912052384768124667089622276645554263637096315789981311223279294139677195180738475072577134102346749289434060321004714706929560791763626145777474484563
```

## 6) Key detail for decrypting GPG
Using S directly as passphrase failed.

Correct passphrase was:

```text
SHA-256(S as big-endian bytes)
5edba444d2ecc490bfbbaa37ce1ce7daa1844e4e881bc05cd1cce0f66e91c181
```

Nice touch by author here. Respect.

## 7) Decrypt and get flag
In Python, once I computed passphrase:

```bash
python3 - << 'PY'
import hashlib
S = 2917912052384768124667089622276645554263637096315789981311223279294139677195180738475072577134102346749289434060321004714706929560791763626145777474484563
s_bytes = S.to_bytes((S.bit_length()+7)//8, 'big')
print(hashlib.sha256(s_bytes).hexdigest())
PY
```

Output:

```text
5edba444d2ecc490bfbbaa37ce1ce7daa1844e4e881bc05cd1cce0f66e91c181
```

Then decrypt:

```bash
gpg --batch --yes --passphrase "5edba444d2ecc490bfbbaa37ce1ce7daa1844e4e881bc05cd1cce0f66e91c181" -o flag.txt -d flag.txt.gpg
cat flag.txt
```

Flag:

```text
hackzero{br41nfuck_is_not_r34l!}
```

### Minimal solve script (all-in-one)

```python
python3 - << 'PY'
import math, hashlib
p=8736489073805684086305179507451312145336960198850222450321684285045258466628525808781552246900007804506276394992600728538533608361706639189532331964901531
g=2
A=2794996066442934640383396708993220584783762169186726070188366297468316333265452428474082701535690342706174889597372484008702943319781202470240884210613693
B=1210454350578824211787039637709213524440747952483197066710749405257527570548081311766060600166395746681022324544415844366753788799012419699450666

def bsgs(y, N):
    m = int(math.isqrt(N)) + 1
    table = {}
    e = 1
    for j in range(m):
        if e not in table:
            table[e] = j
        e = (e * g) % p
    inv = pow(pow(g, m, p), p-2, p)
    gamma = y
    for i in range(m+1):
        if gamma in table:
            x = i*m + table[gamma]
            if x < N and pow(g, x, p) == y:
                return x
        gamma = (gamma * inv) % p
    return None

N = 1 << 32
a = bsgs(A, N)
b = bsgs(B, N)
S = pow(B, a, p)
print("a =", a)
print("b =", b)
print("S =", S)

s_bytes = S.to_bytes((S.bit_length()+7)//8, 'big')
pw = hashlib.sha256(s_bytes).hexdigest()
print("passphrase =", pw)
PY
```

## Analysis
I used ai to write the script, other recons and understandings were done manually. 

By understanding the algo implemented is fine, but they way it is , wrong.
DH was used, but small private exponents made discrete log practical.

## Author

ret2.libc
