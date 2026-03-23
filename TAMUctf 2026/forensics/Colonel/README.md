# Colonel

| Field      | Value |
|------------|-------|
| Category   | forensics |
| Points     | 56 |
| Solves     | 173 |

## Description

<p>Author: <code>Archan6el</code></p><p>An Army Colonel is having trouble decrypting a sensitive file. He remembers it being encrypted with AES CBC with an iv of <code>1234567890123456</code>, but can't for the life of him remember what key he used. He captured a memory dump while he was trying to decrypt the file. Maybe you can find something in there?</p><p>Link to file download is <a href="https://drive.google.com/file/d/1T7dXEyVd0Jmk0dYk8jMMBflJ59Zy88xq/view?usp=sharing">here</a></p>

## Artifacts

- [recover_flag.py](./artifacts/recover_flag.py)
- [kernel_log_excerpt.txt](./artifacts/kernel_log_excerpt.txt)
- [key_reconstruction.txt](./artifacts/key_reconstruction.txt)
- [flag_plaintext.txt](./artifacts/flag_plaintext.txt)

## Writeup

### Flag

```text
gigem{bl3ss3d_4r3_th3_c010n31_m33k}
```

### Executive Summary

The challenge description gives us two key pieces:
1. AES-CBC encryption with IV `1234567890123456`
2. A memory dump to analyze

From there, we know the only unknown is the key. But the challenge also gives us `vmlinux` and `System.map`, which tells us this is a Linux kernel dump worth analyzing with Volatility, not just random userspace memory.

The kernel logs gave us the real break: a validation module logged two failed key attempts and spelled out which character positions were wrong in each. Instead of brute-forcing a key from 8GB of RAM, we just had to merge two almost-correct strings.

### How It Worked

This boils down to bad logging practices in the validation module. It logged both the wrong keys and exactly which positions were bad:

1. We get `System.map` and `vmlinux` — clear signal this is a Linux kernel dump worth Volatility analysis
2. Kernel logs give us two validation attempts with candidate keys in hex
3. Each attempt tells us which indices were wrong
4. We merge them: for positions marked wrong in attempt #1, trust attempt #2; for positions wrong in attempt #2, trust attempt #1
5. Everything else already matched anyway

Once we have the merged key, padding is the only gotcha. The first OpenSSL decrypt failed, but it turned out the file used zero-padding, not PKCS#7. Adding `-nopad` fixed it.

### Getting the Flag

First, unpack and triage:

```bash
tar -xvf colonel.tar.gz
file memory.dump
```

Kernel VM image, so Volatility gets the symbol profile:

```bash
dwarf2json linux --elf vmlinux --system-map System.map > colonel.json
```

The kernel messages give us the critical info—the validation module logged this:

```text
Reading from validation
Error: Invalid key 51782b4b765251314e32525236364978534d35566a6b72474b67303946483266, indices 9 21 31 incorrect
Validation failed
Reading from validation2
Error: Invalid key 58782b4b765251314e51525235364978534d35566a6a72524b673039466c3265, indices 0 12 23 29 incorrect
```

Decode those hex strings:

```python
bytes.fromhex("51782b4b765251314e32525236364978534d35566a6b72474b67303946483266").decode()
# Qx+KvRQ1N2RR66IxSM5VjkrGKg09FH2f

bytes.fromhex("58782b4b765251314e51525235364978534d35566a6a72524b673039466c3265").decode()
# Xx+KvRQ1NQRR56IxSM5VjjrRKg09Fl2e
```

Then I merged them using the logged bad-index sets:

```python
k1 = "Qx+KvRQ1N2RR66IxSM5VjkrGKg09FH2f"
k2 = "Xx+KvRQ1NQRR56IxSM5VjjrRKg09Fl2e"

bad1 = {9, 21, 31}
bad2 = {0, 12, 23, 29}

merged = []
for i, (a, b) in enumerate(zip(k1, k2)):
    if i in bad1:
        merged.append(b)
    elif i in bad2:
        merged.append(a)
    else:
        merged.append(a)  # they match anyway

key = "".join(merged)
print(key)
# Qx+KvRQ1NQRR66IxSM5VjjrGKg09FH2e
```

Then decrypt:

```bash
KEY='Qx+KvRQ1NQRR66IxSM5VjjrGKg09FH2e'
IV='1234567890123456'

openssl enc -d -aes-256-cbc \
  -K "$(printf '%s' "$KEY" | xxd -p -c 256)" \
  -iv "$(printf '%s' "$IV" | xxd -p -c 256)" \
  -nopad \
  -in flag.enc
```

The `-nopad` is critical. The file uses zero-padding, not PKCS#7, so standard decryption gives garbage.

### Final Result

Decrypt output:

```text
gigem{bl3ss3d_4r3_th3_c010n31_m33k}\x00\x00\x00...
```

Trimmed the NULs and got the flag.
