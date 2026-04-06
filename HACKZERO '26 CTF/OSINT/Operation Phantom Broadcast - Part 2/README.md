# Operation Phantom Broadcast : Part 2

| Field      | Value |
|------------|-------|
| Category   | OSINT |
| Points     | 150 |
| Solves     | 99 |

## Description

Identify the malicious package name.

Flag Format:
`hackzero{com.example.com}`

## Writeup

Operation Phantom Broadcast 



I had to find the malicious Android package name.

Flag format:

hackzero{com.example.com}

My Method
I solved this using OSINT, i.e., which mean checking public threat reports and linking IOCs.

I started from campaign context (Part 1 trail), then moved to deeper malware analysis.
In the Acronis report, I checked Android sample details and looked for app identifiers.

For Android, the package name is the unique app ID, i.e., which mean something like com.app.name.

From the analysis trail, I got:

com.red.alertx

So the flag is:

hackzero{com.red.alertx}

Tools I Used
Browser (for threat-report reading)
curl (fetch report pages)
grep (find keywords fast)
apktool (optional APK static check)
aapt (optional package extraction)
gdb was not needed here, i.e., which mean this is not native binary debugging.

Repro Steps (Kali Commands)
# 1) Pull report page locally
curl -L "https://<acronis-report-url>" -o acronis_report.html

# 2) Hunt package-like strings in report text
grep -Eo 'com\.[a-zA-Z0-9_.]+' acronis_report.html | sort -u

# 3) If APK is available, verify package directly
apktool d sample.apk -o sample_decoded

# 4) Check AndroidManifest for package id
grep -R "manifest package=" -n sample_decoded/AndroidManifest.xml

# 5) Alternative direct method
aapt dump badging sample.apk | grep package
Expected package value to confirm:

com.red.alertx

Final Flag
hackzero{com.red.alertx}

## Author

ret2.libc
