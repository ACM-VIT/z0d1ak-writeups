# Gosudartveny bol'she nichego ne govorit!

| Field      | Value |
|------------|-------|
| Category   | Cryptography |
| Points     | 100 |
| Solves     | 58 |

## Description

A really ominous looking cryptographic algorithm.

`secret = "004A742DE34C8A7DA95AE34C95691DA554F72A9F5F2D98DA5603A594F547E59C" `
`ciphertext =  "67ABD4932718A02A4254EEA8BB737D3F4494B4E65A77C38131C270C2C6C07842"`

## Writeup

> ```Flag:```  `hackzero{g05t_15_th3_g04t}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Gosudartveny bol'she nichego ne govorit!
- **Category:** Cryptography
- **Points:** 100
- **Author:** @AnkitS01
- **Solved By:** ret2.libc

I really liked this challenge name. Big respect to the author, very nice hint and very clean crypto design.

## Challenge data
I got two hex strings:

```text
secret = 004A742DE34C8A7DA95AE34C95691DA554F72A9F5F2D98DA5603A594F547E59C
ciphertext = 67ABD4932718A02A4254EEA8BB737D3F4494B4E65A77C38131C270C2C6C07842
```

The line “Gosudartveny…” gave me Russian vibe, i.e., which means this is likely a GOST crypto challenge.

## My thought process
Both values are 64 hex chars, i.e., 32 bytes each.
secret length is 32 bytes, which means it can be a GOST key size.
I first tested easy stuff (XOR, AES guesses), no readable output.
Then I moved to GOST 28147-89 (classic Russian block cipher in many CTFs).
I tested multiple S-box sets and found readable plaintext.
Very nice challenge design from the author, because the hint is enough if I pay attention.

## Environment (Kali VM)
I did this in Kali using Python 3.

```text
python3 --version
sudo apt update
sudo apt install -y git python3-pip
```

## Tool I used (and substitute options)
Main tool I used:

- pygost (Python library), from source clone

Substitute tools I could use:

- gostsum / OpenSSL with GOST engine (if available)
- CyberChef (for quick hex / XOR sanity checks)
- custom Python implementation of GOST block + S-box loop

## Reproduction steps in Kali
1. Clone pygost

```bash
git clone https://github.com/mosquito/pygost.git
```

2. Run solver script

```bash
cd pygost
python3 - << 'PY'
import sys
sys.path.insert(0, ".")
from pygost import gost28147

secret = bytes.fromhex("004A742DE34C8A7DA95AE34C95691DA554F72A9F5F2D98DA5603A594F547E59C")
ciphertext = bytes.fromhex("67ABD4932718A02A4254EEA8BB737D3F4494B4E65A77C38131C270C2C6C07842")

# Try all built-in S-box sets
for sbox in gost28147.SBOXES.keys():
    pt = gost28147.ecb_decrypt(secret, ciphertext, sbox=sbox)
    if b"{" in pt and b"}" in pt:
        print("SBOX:", sbox)
        print("Plain:", pt)
PY
```

## Output I got

```text
Plain: b'hackzero{g05t_15_th3_g04t}\x06\x06\x06\x06\x06\x06'
```

The last \x06 bytes are padding, i.e., which means padded block data.
So final flag is:

```text
hackzero{g05t_15_th3_g04t}
```

## Final notes
This was a very good crypto challenge:

- hint was short but meaningful
- rabbit holes exist but fair
- final solve path is elegant

## Author

ret2.libc
