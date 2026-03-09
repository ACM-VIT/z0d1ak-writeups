# z0d1ac CTF Writeups

This repository contains CTF event setup material and challenge writeups created by **Team z0d1ak**.

## Purpose

The repo is organized to help you:

- create a folder for each CTF event
- track event metadata in an event-level `README.md`
- create category folders for manual writeups
- optionally pull solved challenges from CTFd events
- keep challenge writeups separate and easy to review in git history

## Repository Structure

A typical event layout looks like this:

```/dev/null/example.txt#L1-9
Event Name/
├── README.md
├── web/
│   └── Challenge Name/
│       └── README.md
├── pwn/
└── crypto/
```

- The event-level `README.md` stores event information such as links, timing, format, and description.
- Challenge writeups live deeper in the tree, typically at:

```/dev/null/example.txt#L1-1
<Event>/<Category>/<Challenge>/README.md
```

## `add_comp.sh`

Use `add_comp.sh` to bootstrap a new competition from a CTFtime event URL.

### Basic usage

```/dev/null/example.sh#L1-1
./add_comp.sh <ctftime_event_url>
```

Example:

```/dev/null/example.sh#L1-1
./add_comp.sh https://ctftime.org/event/3171/
```

### What it does

`add_comp.sh` will:

1. fetch event metadata from the CTFtime API
2. create an event directory named after the event title
3. generate an event-level `README.md`
4. ask whether the event uses CTFd
5. do one of the following:
   - **non-CTFd flow:** let you select default categories from `categories.txt` and optionally add extra categories
   - **CTFd flow:** optionally use a player token to fetch solved challenges, create challenge folders, generate challenge `README.md` files, and download challenge files

### Summary of options

When you run the script, you will be prompted for:

- **CTFtime event URL**  
  Required. Used to fetch the event metadata.

- **Uses CTFd?**  
  Choose whether the event runs on CTFd.

- **CTFd base URL**  
  If the event uses CTFd, you can confirm or override the detected site URL.

- **Player API token**  
  Optional. If provided, the script can fetch solved challenges from the CTFd API.

- **Default categories selection**  
  For non-CTFd events, you can interactively choose categories from `categories.txt`.

- **Extra categories**  
  For non-CTFd events, you can add additional comma-separated category names.

## Commit Workflow

This repository is intended to keep event setup and writeup content in separate commits.

### Recommended workflow

1. **Create the event scaffold first**
   - run `add_comp.sh`
   - review the generated event directory and event-level `README.md`
   - commit that event setup as its own commit

2. **Add challenge writeups later**
   - update challenge folders and challenge `README.md` files
   - commit writeups separately from the initial event scaffold

### Why separate commits?

Keeping event creation and writeups in different commits makes it easier to:

- review repository history
- see when an event was added
- track writeup progress over time
- avoid mixing setup changes with solution content

## Author Injection Hook

This repo includes a pre-commit hook that can inject an `## Author` section into newly added challenge writeups.

The intended behavior is:

- event-level `README.md` changes should be committed first
- challenge writeups should be committed afterward
- if the event-level `README.md` is not part of the commit, writeup author injection may be skipped depending on the hook logic

This supports the workflow of making one commit for the event, then separate commits for individual writeups.

## Team

Writeups in this repository are maintained by **Team z0d1ak**.
