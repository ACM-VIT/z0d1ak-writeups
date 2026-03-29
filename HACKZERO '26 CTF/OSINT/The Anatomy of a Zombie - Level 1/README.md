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

### Flag
```
hackzero{Ch_2.14.1_thumb.dd}
```

### Executive Summary

This challenge focused on identifying a worm involved in the 2008 breach of US military networks and extracting key technical details about its evolution. By analyzing the clues and using open-source intelligence, the worm was identified as Agent.BTZ. The task required finding its final version before redevelopment and the log file it created on infected USB drives.

### Vulnerability Analysis

The worm described spreads through USB drives and targets air-gapped systems. This behavior is strongly associated with Agent.BTZ. It exploited the trust in removable media to bypass network defenses.

The malware also stored data about infected systems using hidden files on USB drives. This creates a traceable artifact that can be studied through malware analysis reports.

### Exploit Strategy

The solution followed a structured approach:

1. Identify the malware using the historical context and behavior.
2. Research its development timeline.
3. Locate the final version released before the developers changed architecture.
4. Identify the log file used for tracking infections.

Threat intelligence reports confirmed that the final major version before the rewrite was Ch 2.14.1. The worm created a hidden file named thumb.dd to store logs.

### Implementation

The process involved:

* Searching for information about the 2008 military malware incident.
* Mapping the behavior to Agent.BTZ.
* Reviewing security research papers and blogs describing its versions.
* Extracting the required details from reliable sources.

### Execution and Results

The gathered information matched all clues in the challenge. The final version string and log file name were combined to form the correct flag.
 Strategy


