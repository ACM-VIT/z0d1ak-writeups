# Operation Phantom Broadcast : Finale

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 150 |
| Solves     | 97 |

## Description

Identify the C2 domain url.

Flag Format:
`hackzero{domainname.tld}`

## Writeup

Operation Phantom Broadcast 
I had to identify the C2 domain URL.

Flag format:

hackzero{domainname.tld}

My Thinking
In this part, I made sure I did not confuse two things:

Payload distribution domain = where malware is hosted/downloaded
C2 (Command and Control) = which mean the server malware talks to after infection
I followed the malware-analysis path and checked infrastructure details in technical reporting.
From the C2/network section, I got the active C2 domain:

api.ra-backup.com

So the flag is:

hackzero{api.ra-backup.com}

Tools I Used
Browser for report reading
curl for local copy of report
grep for IOC extraction
Optional: whois, dig, nslookup for infra checks
Optional malware triage: apktool, jadx
gdb was not needed here, i.e., which mean this challenge was IOC/intel focused, not native debugging.

Repro Steps (Kali Commands)
# 1) Pull malware analysis page
curl -L "https://<analysis-url>" -o analysis.html

# 2) Extract domain-like values
grep -Eo '([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}' analysis.html | sort -u

# 3) Find C2-related context
grep -iE "c2|command|control|api|beacon|exfil|server" analysis.html

# 4) Quick infra validation
whois api.ra-backup.com
dig +short api.ra-backup.com
nslookup api.ra-backup.com
Final Flag
hackzero{api.ra-backup.com}

## Author

ret2.libc
