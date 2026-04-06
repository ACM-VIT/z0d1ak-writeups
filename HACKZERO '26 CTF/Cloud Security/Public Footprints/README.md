# Public Footprints

| Field      | Value |
|------------|-------|
| Category   | Cloud Security |
| Points     | 150 |
| Solves     | 78 |

## Description

A noisy public container hides more than it show. Trace the right files to uncover what was never meant to be exposed.

Flag Format:
`hackzero{}`

**Challenge URL**: https://leakyleak.blob.core.windows.net/public/

## Writeup

> ```Flag:```  `hackzero{9b558d507bb36c7a4ea4d9854f735e59}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Public Footprints
- **Category:** Cloud Security
- **Points:** 150
- **Author:** @pphreak_1001
- **Solved By:** ret2.libc


At first it looked like random text-file spam, but the real issue was credential leakage.

## Challenge details

- **Challenge URL:** `https://leakyleak.blob.core.windows.net/public/`
- **Flag format:** `hackzero{}`

## Approach

I used a simple workflow> enumerate the public container, filter noise, and follow the leaked secret.

### 1. Enumerate the public container

First I listed all blobs/files inside the public container.

```bash
curl -s "https://leakyleak.blob.core.windows.net/public/?restype=container&comp=list"
```

The response returned XML with many filenames. There were a lot of decoy `.txt` files, and one very interesting file: `.env`.

To extract the blob names quickly:

```bash
curl -s "https://leakyleak.blob.core.windows.net/public/?restype=container&comp=list" \
  | grep -oP '(?<=<Name>).*?(?=</Name>)'
```

### 2. Pull likely sensitive files

In this kind of challenge, I always check:

- `.env`
- `hint.txt`
- any file named `token`, `secret`, `config`, or `auth`

Commands:

```bash
curl -s "https://leakyleak.blob.core.windows.net/public/.env"
curl -s "https://leakyleak.blob.core.windows.net/public/hint.txt"
```

Important findings:

- `.env` contained `SAS_TOKEN=...`
- `hint.txt` pointed to a private blob URL:
  `https://<account>.blob.core.windows.net/private-data/flag.txt`

That clearly mean that the flag path was not publicly accessible, and we needed authenticated read access using the leaked token.

### 3. Understanding the SAS token

A SAS token is a Shared Access Signature for Azure Storage. It grants temporary signed permissions.

Key fields in the token are..

- `sp=r` — read permission
- `st=...` — start time
- `se=...` — expiry time
- `sr=b` — blob-level access
- `sig=...` — signature

If the current time is between `st` and `se`, the URL access should work.

### 4. Building the final flag URL

The account name from the challenge URL is `leakyleak`.

So I thought as a guess and replaced `<account>` with `leakyleak` and appended the leaked SAS token as the query string.

```bash
SAS='sp=r&st=2026-03-26T09:22:51Z&se=2026-03-31T17:37:51Z&spr=https&sv=2024-11-04&sr=b&sig=zSBn28Brkpy11NqL7MpbtgmJ%2FN1%2B37%2FX%2BD3IgTjVSKk%3D'

curl -s "https://leakyleak.blob.core.windows.net/private-data/flag.txt?$SAS"
```

The response returned the flag directly.

## Flag

`hackzero{9b558d507bb36c7a4ea4d9854f735e59}`

## Analysis


1. The Public container was allowed enumeration.
2. also, sensitive `.env` file was exposed in the public scope.
3. The `.env` leaked a live SAS token.
4. And token had read permission for a private blob.
5. Finally private flag file became directly reachable.

This challenge demonstrated a cloud misconfiguration combined with secret exposure.

## Author

ret2.libc
