# Operation Vandal

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 250 |
| Solves     | 21 |

## Description

A threat intelligence brief reveals suspicious infrastructure and an operator footprint. Analyze the provided artifact, pivot across identities and infrastructure, and attribute the operation.

A threat intelligence team has intercepted fragments of an intrusion campaign involving suspicious infrastructure and developer activity. Initial findings suggest the presence of a staging environment and an operator-linked identity. The activity appears coordinated but attribution remains incomplete.

Flag Format: 
`hackzero{<alias>_<ip_without_dots>}`

## Files

- [Incident_Report_Internal_Use_Only.pdf](./Incident_Report_Internal_Use_Only.pdf)

## Writeup

> ```Flag:```  `hackzero{vandal_ops_99_1852251723}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Operation Vandal
- **Category:** OSINT
- **Points:** 250
- **Author:** Sahasra(@CipherNyx)
- **Solved By:** ret2.libc


I have to attribute an intrusion operation using one provided artifact and OSINT pivots, then build a flag in this format:

hackzero{<alias>_<ip_without_dots>}

## 2) Starting with Evidence
The initial artifact was a PDF intelligence brief.
Visible clues from the document included:

- Suspicious domain: `sync-node[.]net`
- Operational hint: `ref: vandal`
- Mention of staging/deployment traces

At first, the URLs/IP section looked empty in the visible text, so the investigation moved to metadata and pivots.

## 3) Metadata and Identity Pivot
The PDF metadata exposed a strong operator identity:

- Author: `vandal_ops_99@gmail.com`
- Creator: `Vandal Research Unit`

This gave us a concrete alias family: vandal, vandal_ops_99, and vandal-ops-99.

## 4) Infrastructure Pivot
The domain `sync-node.net` did not provide a stable direct A record during live DNS checks, so we pivoted through deployment/config traces.

A config artifact was found in a public GitHub repo:

- `ENV=staging`
- `SYNC_TARGET=sync-node[.]net`
- `PORTAL=vandal-secure-portal[.]net`
- `CONFIG=https://l1nk.dev/0AAAAAD1A3s8-IP-1852251723-N4j4peMiViaXvP364249H`

The shortlink later redirected to a Google Drive-hosted JPEG containing the same deployment context and masked backup IP line.
The key encoded indicator in the shortlink was:

- `IP-1852251723`

This decodes to dotted IPv4 as:

- `185.225.17.23`

## 5) Attribution Logic
Attribution was based on combining identity + infra:

- Identity side: `vandal_ops_99@gmail.com`, `vandal-ops-99`
- Infra side: staging target `sync-node[.]net` + encoded backup IP `185.225.17.23`

Most precise alias for flag construction: `vandal_ops_99`

## 6) Flag Construction
Required format removes dots from IP:

- Alias: `vandal_ops_99`
- IP without dots: `1852251723`

Final flag:

hackzero{vandal_ops_99_1852251723}

## 7) Final Answer
hackzero{vandal_ops_99_1852251723}

### References
- GitHub config page: https://github.com/vandal-ops-99/portal-sync/blob/main/config.txt
- Raw config: https://raw.githubusercontent.com/vandal-ops-99/portal-sync/main/config.txt
- Shortlink used in config: https://l1nk.dev/0AAAAAD1A3s8-IP-1852251723-N4j4peMiViaXvP364249H
- Redirect destination (shared during solving): https://drive.google.com/file/d/17zqFa4RJsPeusZqlnELaeyFRuVanrtiq/view?usp=sharing

## Author

ret2.libc
