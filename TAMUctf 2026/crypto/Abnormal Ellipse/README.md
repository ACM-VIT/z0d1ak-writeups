# Abnormal Ellipse

| Field      | Value |
|------------|-------|
| Category   | crypto |
| Points     | 50 |
| Solves     | 395 |

## Description

<p>Author: <code>Marfung37</code></p><p>Some reason people are using these weird ellipses to do their encryption. But aren't quadratic curves completely broken. Anyways, I caught the data that was being sent along with how they are doing the encryption.</p>

## Files

- [abnormal-ellipse.tar.gz](./abnormal-ellipse.tar.gz)

## Writeup

### Flag

```text
gigem{an0ma1ou5_curv3_ss5a_d41z8GaFF3kZ8}
```

### Executive Summary

This challenge uses ECDH on a custom elliptic curve to derive an AES-CBC key, then encrypts the flag.

At first glance, solving ECDH should require breaking elliptic-curve discrete log, which is supposed to be hard. But the challenge title and hint about "abnormal ellipses" point to anomalous elliptic curves, where the curve order is exactly equal to the field prime ($|E(\mathbb{F}_p)|=p$).

For anomalous curves, Smart's attack reduces ECDLP to arithmetic over $\mathbb{Z}/p^2\mathbb{Z}$ and recovers private scalars efficiently. Once one scalar is recovered, the shared secret follows immediately, and AES decryption reveals the flag.

### Vulnerability Analysis

The provided code:

1. Defines a custom curve $E: y^2=x^3+ax+b \pmod p$
2. Picks random base point $G$
3. Generates private keys $d_A,d_B$
4. Publishes $P_A=d_A G$ and $P_B=d_B G$
5. Derives AES key from $x(d_B P_A)$

Normally this is secure, but the curve is anomalous. In that setting, ECDLP can be solved in polynomial time with Smart's attack.

The core weakness is not AES or CBC mode, but weak curve selection. A custom curve without order validation is dangerous, and anomalous curves are a known forbidden class.

### Exploit Strategy

1. Parse $p,a,b,G,P_A,P_B$, ciphertext, and IV from challenge files.
2. Use Smart's anomalous-curve method to solve:
   - $d_A$ from $(G,P_A)$
   - optionally $d_B$ from $(G,P_B)$ for cross-check
3. Compute shared secret point $S=d_A P_B$.
4. Hash $x(S)$ with SHA-256 to get AES-256 key.
5. Decrypt with AES-CBC and remove PKCS#7 padding.

Smart attack outline used here:

1. Lift points from $\mathbb{F}_p$ to solutions modulo $p^2$ via Hensel-style correction on $y$.
2. Compute $p\cdot\widetilde{G}$ and $p\cdot\widetilde{Q}$ on the lifted curve over $\mathbb{Z}/p^2\mathbb{Z}$.
3. Map these into $\mathbb{F}_p$ with:

$$
\phi(R)= -\frac{X_R\cdot (Z_R/p)}{Y_R} \pmod p
$$

for Jacobian coordinates $R=(X_R:Y_R:Z_R)$.

4. Recover scalar $k$ from $Q=kG$ as:

$$
k = \phi(p\widetilde{Q}) \cdot \phi(p\widetilde{G})^{-1} \pmod p
$$

### Implementation

I implemented a standalone Python solver that:

1. Implements elliptic curve arithmetic in affine coordinates mod $p$.
2. Implements Jacobian arithmetic mod $p^2$ for lifted-point multiplication.
3. Lifts points from mod $p$ to mod $p^2$.
4. Applies the anomalous map to recover discrete logs.
5. Reconstructs the shared key and decrypts ciphertext with `cryptography`.

Key recovered values from execution:

- $d_A =$ `5302515257459728333067206555460709176819601641952986275899160992587299740102`
- $d_B =$ `14351322784803667778298934151869100639090151998944262589608260939971387880030`

### Execution & Results

Running the solver produced plaintext:

```text
gigem{an0ma1ou5_curv3_ss5a_d41z8GaFF3kZ8}
```

Final flag:

```text
gigem{an0ma1ou5_curv3_ss5a_d41z8GaFF3kZ8}
```
