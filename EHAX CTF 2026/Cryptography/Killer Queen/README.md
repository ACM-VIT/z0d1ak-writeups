# Killer Queen

| Field      | Value |
|------------|-------|
| Category   | Cryptography |
| Points     | 487 |
| Solves     | 27 |

## Description

`author: MrFahrenheit and CyC`

She keeps her Moet et Chandon in her pretty cabinet.

Nothing she offers is accidental. Nothing she withholds is without reason.

Recommended at the price, insatiable an appetite - wanna try?

`nc 20.244.7.184 7331`

## Files

- [Handout.zip](./Handout.zip)

## Writeup

### Flag

```text
EH4X{Cav1aR_c1Gar3TT3s_Ch3bYsH3V_05091946}
```

### Executive Summary

The service combines Chebyshev-polynomial oracles with a two-layer encryption pipeline. A single oracle call (`q=1`) leaks the hidden Chebyshev root `c`, which is enough to reconstruct both layers and recover the plaintext flag.

### Vulnerability Analysis

From interaction and handout hints:

- `pretty_cabinet(q)` behaves as `T_q(v) mod p`.
- `moet_chandon(q)` behaves as `T_q(c) mod p` for secret `c`.
- Because `T_1(x) = x`, querying `moet_chandon(1)` reveals `c` directly.

This collapses the intended hardness. Once `c` is known, both key derivation and stream generation become deterministic.

### Exploit Strategy

1. Connect to service and request `q=1`.
2. Parse `p`, `iv`, `ciphertext`, and leaked `c`.
3. Derive outer AES key:
   - `K2 = SHA256(str(c))[:16]`
4. AES-CBC decrypt ciphertext and remove PKCS#7 padding to obtain intermediate bytes.
5. Regenerate inner XOR keystream from Chebyshev sequence at root `c`:
   - `T_0=1`, `T_1=c`
   - `T_n = 2*c*T_{n-1} - T_{n-2} (mod p)`
   - per term chunk: `SHA256(str(T_n))[:16]`
6. XOR intermediate bytes with keystream to recover final flag.

### Implementation

Minimal interaction pattern:

```bash
printf '1\nexit\n' | nc 20.244.7.184 7331
```

Then apply offline decryption with the recurrence above. Only one oracle query is required.

### Execution & Results

The reconstructed pipeline consistently decodes the published ciphertext to the final flag.

