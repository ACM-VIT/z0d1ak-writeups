# The Anatomy of a Zombie : Level 2

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 25 |
| Solves     | 151 |

## Description

Everyone knows that the 2008 Agent.btz worm left behind a hidden log file named thumb.dd on infected USB drives to track its victims. However, thumb.dd wasn't just a flat text file; it was actually a container holding a specific archive format, which internally concealed three distinct files containing the stolen system data and activity logs.

What archive format was stored inside thumb.dd, and what was the exact filename (including extension) of the .ocx file hidden inside it?

Flag Format:
`hackzero{ArchiveFormat_FileName.ocx}`

## Writeup

### Flag

```
hackzero{CAB_winview.ocx}
```

### Executive Summary

This challenge required analyzing the internal structure of the log file used by Agent.BTZ. The task was to determine the archive format stored inside the file and identify a specific file contained within it.

### Vulnerability Analysis

The file thumb.dd was not a simple log file. Instead, it acted as a container for structured data. This indicates that the malware used an archive format to organize stolen information.

Such behavior helps attackers manage multiple data components while keeping them hidden within a single file.

### Exploit Strategy

The approach was:

1. Investigate technical analyses of Agent.BTZ.
2. Identify how thumb.dd stores data internally.
3. Extract the archive format used.
4. List the files contained inside the archive.
5. Select the required .ocx file.

Research showed that thumb.dd contains a CAB archive. Inside it were multiple files, including winview.ocx.

### Implementation

Steps followed:

* Search for detailed malware analysis reports of Agent.BTZ.
* Focus on file structure and data storage behavior.
* Identify references to thumb.dd contents.
* Extract the archive type and file names.

### Execution and Results

The archive format and file name matched the challenge requirements. Combining them produced the correct flag.

