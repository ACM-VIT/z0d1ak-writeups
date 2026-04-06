# Operation Phantom Broadcast : Part 1

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 150 |
| Solves     | 106 |

## Description

A recent alert circulating on social media highlights a suspicious mobile application being distributed under the guise of an emergency notification. The indicator shared is only part of a larger campaign. Identify the domain used to distribute the payload, as observed in the original reporting of this activity.


Flag format:
`hackzero{domainname.tld}`

## Writeup

## Challenge

We had to find the payload distribution domain from the original reporting of a fake emergency alert mobile app campaign.

Flag format was:

`hackzero{domainname.tld}`

## My Approach

I treated this as an OSINT challenge

I focused on the clue words:
- suspicious mobile app
- fake emergency alert
- social media warning
- original reporting

Then I searched for the campaign writeup and checked IOC details, i.e., Indicators of Compromise, which means technical traces like domain, IP, URL, hash.



## Reproducible Steps (Kali Commands)

```bash
# 1) Start with targeted searches (manual in browser)
# Example query used:
# "fake emergency alert app cloudsek"
# "payload distribution domain emergency notification malware"

# 2) Once original report URL is found, pull page text
curl -L "https://www.cloudsek.com/blog/<report-path>" -o report.html

# 3) Extract suspicious domains quickly
grep -Eo '([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}' report.html | sort -u

# 4) Optional: search for delivery/download keywords near domain mentions
grep -iE "apk|payload|download|distribution|ioc" report.html

# 5) Optional verification
whois shirideitch.com
```

## What I Found

From the original reporting section on payload/app delivery, I identified the distribution domain as:

`shirideitch.com`

So the flag is:

`hackzero{shirideitch.com}`

## Author

ret2.libc
