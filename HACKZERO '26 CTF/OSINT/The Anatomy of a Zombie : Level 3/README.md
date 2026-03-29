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

```

### Executive Summary


### Vulnerability Analysis


### Exploit Strategy


### Implementation


### Execution & Results


