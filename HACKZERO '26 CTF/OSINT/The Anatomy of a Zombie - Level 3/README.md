# The Anatomy of a Zombie : Level 3

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 50 |
| Solves     | 150 |

## Description

Fast forward to 2017. The developers had abandoned USB worms and deployed ComRAT v4. This variant famously bypassed network defenses by hijacking the Gmail basic HTML interface to receive commands. To do this, it didn't just scrape text blindly; it relied on a specific open-source C library developed by Google to parse the HTML tree of the Gmail inbox. Furthermore, the commands it downloaded from the inbox were disguised as malicious email attachments using a very common office file extension.

Name the specific open-source HTML parsing library ComRAT v4 utilized, and the file extension it used to disguise its command attachments.

Flag Format:
`hackzero{LibraryName_Extension}`
**(Library name as it is, extension in lowercase without the dot).**

## Writeup

### Flag

```
hackzero{Gumbo_docx}
```

### Executive Summary

This challenge moved to a later stage of the same malware family, focusing on ComRAT v4. The goal was to identify the HTML parsing library used by the malware and the file extension used to disguise command data.

### Vulnerability Analysis

ComRAT v4 used Gmail as a command and control channel. It accessed the Gmail basic HTML interface to receive commands. To do this reliably, it needed to parse HTML content programmatically.

Instead of building a custom parser, the malware used an existing open-source library. This introduces a dependency that can be identified through reverse engineering.

Commands were hidden as email attachments, disguised using common file extensions to avoid suspicion.

### Exploit Strategy

The process was:

1. Identify ComRAT v4 from the description.
2. Locate detailed technical reports about its behavior.
3. Find references to embedded libraries.
4. Identify how it processes Gmail HTML content.
5. Extract the file extension used for disguised attachments.

Reports confirmed that the malware used the Gumbo HTML parser. The attachments used for commands were disguised as common Office documents with the .docx extension.

### Implementation

Steps included:

* Searching for ComRAT v4 technical analyses.
* Reviewing malware reverse engineering reports.
* Identifying embedded libraries within the binary.
* Extracting details about command delivery methods.

### Execution and Results

The identified library and file extension matched the challenge requirements. Combining them resulted in the correct flag.
