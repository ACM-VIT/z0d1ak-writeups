# Beneath The Surface

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 300 |
| Solves     | 10 |

## Description

The threat actor `Mr0x00` has been observed leaving digital breadcrumbs across the surface web before disappearing into the dark. Intelligence suggests he maintains a public presence on under his known alias. Begin your hunt on the surface. Find him where people dump their secrets publicly. His alias is your first lead. What you find there will point you deeper?

Flag Format:
`hackzero{}`

## Writeup

### Flag

```
hackzero{y0u_c4m3_l0n6_w4y_5urf1n6!}
```

### Executive Summary

This challenge focused on extracting data from a PrivateBin-style encrypted paste using a ladder token and password. Instead of relying on the hosting endpoint, the solution leveraged understanding of client-side decryption.


### Key Assets

* Pastebin profile: [https://pastebin.com/u/mr0x00](https://pastebin.com/u/mr0x00)
* Ladder token:

```
?1e19d28759f16a16#8nmOODgWGbJFVsO/xwAU7xHuI8iwn3Pbgx9gE5czpSg=
```

* Password:

```
NotMuchSecure!
```

* PrivateBin docs: [https://privatebin.info/](https://privatebin.info/)
* GitHub (logic): [https://github.com/PrivateBin/PrivateBin](https://github.com/PrivateBin/PrivateBin)

### Strategy

1. Identify entry point (Pastebin profile).
2. Extract token and password.
3. Recognize PrivateBin format (?id#key).
4. Reproduce decryption locally using known logic.


### Implementation (Step-by-Step)

**Step 1: Surface Recon**
Visited Pastebin profile → found paste containing:

* Password: NotMuchSecure!
* Ladder token

Return: Valid clue confirming deeper encrypted layer.

**Step 2: Identify Format**
Token format:

```
?pasteID#key
```

Return: Recognized as PrivateBin / ZeroBin encrypted paste.


**Step 3: Understand Decryption Model**
From documentation and source:

* Key is stored in URL fragment
* Password adds an extra layer
* Decryption flow:

  1. Decrypt using key
  2. Retry using key + SHA-256(password)
  3. Decompress plaintext

Return: Clear path to manual/local decryption.

**Step 4: Reproduce Decryption Locally**
Inputs used:

* Paste ID: 1e19d28759f16a16
* Key: 8nmOODgWGbJFVsO/xwAU7xHuI8iwn3Pbgx9gE5czpSg=
* Password: NotMuchSecure!

Process:

* Apply key-based AES decryption
* Combine with hashed password
* Decompress payload

Return: Successfully recovered plaintext.

### Execution and Results

Recovered content revealed the final flag:

```
hackzero{y0u_c4m3_l0n6_w4y_5urf1n6!}
```

