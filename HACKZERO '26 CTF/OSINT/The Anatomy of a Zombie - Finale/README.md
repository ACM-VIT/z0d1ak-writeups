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

### Flag
```
hackzero{ethereal.exe_0xC001BA5E}
```

### Executive Summary

This challenge required correlating two different parts of the Turla malware ecosystem. The first part focused on Epic Turla (Wipbot) and its anti-analysis techniques. The second part focused on the Uroburos (Snake) rootkit and how it identifies its own command and control traffic. By combining information from trusted technical reports, both answers were derived accurately.


### Vulnerability Analysis

Epic Turla includes anti-analysis checks to detect whether it is running in a monitored environment. One such method is scanning for packet capture tools. If such tools are found, execution is delayed or altered.

The challenge specifically pointed to a legacy network sniffer that was later rebranded as Wireshark. This narrows the scope significantly and avoids confusion with other tools.

For the second part, the Uroburos rootkit uses a Windows Filtering Platform driver to intercept and process network traffic. It decrypts incoming packets and checks for specific hardcoded markers to identify valid command and control data. These markers are 32-bit hexadecimal constants.


### Exploit Strategy

The solving approach was divided into two independent lookups.

For Epic Turla:

1. Identify the malware family from the name provided.
2. Search for official technical reports describing its behavior.
3. Locate the list of processes checked for packet capture tools.
4. Use the clue about rebranding to select the correct executable.

For Uroburos:

1. Focus on the Windows Filtering Platform driver behavior.
2. Search for documentation mentioning packet markers or magic values.
3. Locate the exact hexadecimal constants used in traffic identification.
4. Extract the second value as required by the challenge.


### Implementation

The process involved targeted OSINT queries and prioritizing primary sources.

For Epic Turla, the Kaspersky technical report was used. It lists multiple packet capture tools checked by the malware, including ethereal.exe, wireshark.exe, tcpdump.exe, and others. Based on the clue, ethereal.exe was selected as the correct answer.

For Uroburos, technical whitepapers and slide decks describing the Snake rootkit were reviewed. These sources explicitly mention two packet markers used by the malware: 0xDEADBEAF and 0xC001BA5E.

The challenge only required the second value, so it was extracted directly without modifying or normalizing it.

---

### Execution and Results

Both components were validated against reliable technical sources. The executable name and hexadecimal value matched the challenge requirements exactly.

Combining them in the required format produced the final flag:
```
hackzero{ethereal.exe_0xC001BA5E}
```
