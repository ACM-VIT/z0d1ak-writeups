# Forge's ....... well forge

| Field      | Value |
|------------|-------|
| Category   | Reverse Engineering |
| Points     | 50 |
| Solves     | 267 |

## Description

Forge has made it so that only his trinket can open his workshop(forge) or so it would seem.

> Author : shura356

## Files

- [forge](./forge)

## Writeup

### Flag

```text
APOORVCTF{Y0u_4ctually_brOught_Y0ur_owN_Firmw4re????!!!}
```

### Executive Summary

`forge` includes anti-debug checks and cleanses sensitive buffers before exit. The reliable solve is dynamic: bypass `PTRACE_TRACEME` failure and hook `OPENSSL_cleanse` to dump memory right before wipe. The dumped buffer contains the full flag.

### Vulnerability Analysis

Key reversing findings:

- Early anti-debug with `ptrace(PTRACE_TRACEME)` and failure exit path.
- Internal string construction and OpenSSL-assisted processing.
- Sensitive material is explicitly erased using `OPENSSL_cleanse`.

This creates a classic extraction point: intercept cleanse to read data before destruction.

### Exploit Strategy

1. Use `LD_PRELOAD` hook library.
2. Override `ptrace` so `PTRACE_TRACEME` always appears successful.
3. Override `OPENSSL_cleanse` to log buffer data before forwarding.
4. Run binary with hooks and inspect dumped ASCII/hex output.

### Implementation

Hook behavior summary:

- `ptrace`: if request is `PTRACE_TRACEME` and original call fails, return `0`.
- `OPENSSL_cleanse(ptr, len)`: print buffer for interesting lengths, then call original.

Execution pattern:

```bash
gcc -shared -fPIC hook.c -o hook.so -ldl
LD_PRELOAD=./hook.so ./forge
```

### Execution & Results

During cleanse interception, a 56-byte buffer reveals the flag shown above.

