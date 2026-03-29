# The Anatomy of a Zombie : Finale

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 100 |
| Solves     | 134 |

## Description

The Turla ecosystem is vast. Before dropping heavy backdoors, the group often deploys a reconnaissance scout known as Epic Turla (or Wipbot). To avoid analysis, this scout delays its execution if it detects certain packet capture tools running on the system—including an older, legacy network sniffer that was eventually rebranded as Wireshark. If the environment is deemed safe and high-value, they deploy the Uroburos (Snake) kernel rootkit. To intercept its own Command & Control data from the network stream, the Uroburos Windows Filtering Platform (WFP) driver decrypts inbound traffic and looks for one of two hardcoded 32-bit hex "magic values." One is `0xDEADBEEF`. The other spells a phrase in leetspeak.

What is the .exe name of the legacy packet sniffer Epic Turla checks for, and what is the second `32-bit` hex magic value Uroburos looks for?

Flag Format:
`hackzero{filename.exe_0xHEXVALUE}` 
**(Hex value strictly in uppercase).**

## Writeup

### Flag

```

```

### Executive Summary


### Vulnerability Analysis


### Exploit Strategy


### Implementation


### Execution & Results


