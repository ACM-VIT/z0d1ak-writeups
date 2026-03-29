# The Anatomy of a Zombie : Level 1

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 25 |
| Solves     | 155 |

## Description

Following the devastating 2008 breach of US military networks in Kabul, the "zombie" worm responsible underwent several iterations. It relied on infecting air-gapped networks via USB drives, leaving behind a very specific hidden log file to track its victims. The original worm code base saw its final major update in early 2010 before the developers went silent to rewrite the architecture.

Identify the internal version string of that final major 2010 iteration, and the name of the specific log file it created on infected USB drives.

Flag Format:
`hackzero{VersionString_Filename.extension}`
`(e.g., CTF{Ch_1.0_log.txt})`

## Writeup

The clue points to Agent.BTZ, on searching major rewrite is Ch 2.14.1 and the artifact is thumb.dd

`https://blog.gdatasoftware.com/2015/01/23927-evolution-of-sophisticated-spyware-from-agent-btz-to-comrat`
`https://securelist.com/agent-btz-a-source-of-inspiration/58551/`


### Flag

```
hackzero{Ch_2.14.1_thumb.dd}
```

### Executive Summary


### Vulnerability Analysis


### Exploit Strategy


### Implementation


### Execution & Results


