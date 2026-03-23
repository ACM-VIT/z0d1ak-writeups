# Phantom

| Field      | Value |
|------------|-------|
| Category   | forensics |
| Points     | 207 |
| Solves     | 44 |
| Author     | cobra |

## Description

> The flag is somewhere around <https://github.com/tamuctf/phantom> or something idk

## Writeup

### Flag

```text
gigem{917hu8_f02k5_423_v32y_1n7323571n9_1d60b3}
```

### Executive Summary

The repository itself was the artifact to investigate. At first, the `phantom` repo seemed completely empty—just a one-line README on `main` with nothing else. No downloadable files, no service to connect to. But the secret was hiding in GitHub's metadata. By looking at public repo events and commit comments, I could find SHAs for orphaned commits that weren't on any visible branch, and GitHub would still return the full commit if I asked for it directly.

There was an obvious path forward: a commit that added `phantom.py` carrying the flag `gigem{gh0st_1n_th3_sh3ll}`. But it turned out to be wrong—someone else had added it. So I had to dig deeper. I looked at every hidden commit referenced in the repo activity and realized the real flag was in a commit made by the repository owner, not in the bait comments people kept adding later.

The real flag was in this commit:

- **Commit:** `b365313472870cbf887a42a7be75df741b60c8d3`
- **Author:** Noah Mustoe (cobradev4)
- **Date:** March 16, 2026

### How It Worked

GitHub exposes more than you think:

1. **Commit comments leak SHAs** — Even commits not on any visible branch show up in repo activity
2. **You can fetch them directly** — If you know the SHA, GitHub gives you the full commit regardless of whether it's on `main`

So the `main` branch was incomplete. The real data was scattered across:
- Repo event history
- Commit comments
- Orphaned commits (if you know the SHA)

The tricky part was separating signal from noise. People had added fake flags in comments claiming the real one was planted by an AI bot, trying to confuse solvers. But the actual commit history didn't lie—Git objects matter more than comments.

### Solve Path

1. Check the challenge description—no downloads, no target service, just a GitHub link
2. Look at the repo—basically empty except for a one-liner README
3. Hunt for hidden commits using GitHub's API
4. Check repo events and commit comments for leaked SHAs
5. Fetch each one and look for actual commit objects
6. Figure out which flag was real:
   - Who wrote the commit?
   - When was it written?
   - Was it the author or someone messing around?
7. Submit the real one

The key was trusting the timeline and authorship. The real flag came from the owner on March 16. The fake claims about it being planted came later, on March 21, after people had started poking around.

### Getting the Flag

Doing some early pathfinding with the repo link via the gh cli

```bash
gh api repos/tamuctf/phantom/contents
gh api repos/tamuctf/phantom/git/matching-refs/
gh api 'repos/tamuctf/phantom/events?per_page=100'
gh api repos/tamuctf/phantom/comments
```

The repo events showed some interesting commit SHAs that had been commented on:

- `161dff9757896db6a9d6956a6e7523c4f8f9fdd3`
- `2efe79cd9caf3f449530e0ceacc25573461d78e7`
- `b365313472870cbf887a42a7be75df741b60c8d3`
- `60d133b63d1f121d9137298e74936e3ffef8c5a6`

Then I grabbed each one:

```bash
gh api repos/tamuctf/phantom/commits/161dff9757896db6a9d6956a6e7523c4f8f9fdd3
gh api repos/tamuctf/phantom/commits/2efe79cd9caf3f449530e0ceacc25573461d78e7
gh api repos/tamuctf/phantom/commits/b365313472870cbf887a42a7be75df741b60c8d3
gh api repos/tamuctf/phantom/commits/60d133b63d1f121d9137298e74936e3ffef8c5a6
```

People were going absolutely crazy trying to solve this. There were fake flags scattered in comments, random PRs nobody needed, forks all over the place. Everyone was just throwing shit at the wall to see what stuck. But the real flag had to be somewhere in the actual repo history.

#### The Real One

When I fetched the owner's commit `b365313...`, it had the flag hidden in a patch:

```text
gigem{917hu8_f02k5_423_v32y_1n7323571n9_1d60b3}
```

I knew this was the right one because:
- It came from the challenge author, not some random person
- It was committed early, way before everyone started planting fake flags
- It was an actual commit, not just people messing around in comments
- The fake flag posts came after, which was sus as hell

### Final Flag

```text
gigem{917hu8_f02k5_423_v32y_1n7323571n9_1d60b3}
```

### Artifacts

I copied the key solve artifacts into this writeup directory under `artifacts/`:

- `artifacts/ch13.json`  
  The canonical CTFd challenge JSON response.

- `artifacts/commit_comment_events.json`  
  A focused extract of the repo event stream showing the commit-comment events that leaked the orphaned SHAs.

- `artifacts/phantom_commit_comments.json`  
  Full commit comment enumeration for the repo.

- `artifacts/commit_b365.json`  
  The owner-authored hidden `Add flag` commit that contained the accepted flag.


### Lessons

- GitHub shows way more than just the main branch
- Commit comments can leak SHAs of commits that don't belong to any branch
- GitHub will hand you the full commit if you ask by SHA
- Always trust the Git history over what people say in comments
- Forensics here meant investigating hidden repo history
