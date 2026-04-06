# Silent Signals in the Noise

| Field      | Value |
|------------|-------|
| Category   | Forensics |
| Points     | 200 |
| Solves     | 38 |

## Description

While analysing network traffic suspected to be linked to an advanced persistent threat (APT), everything appears to blend into normal activity, HTTP requests, random connections, and routine chatter. Yet something feels off. Beneath this seemingly harmless traffic, a hidden communication may be taking place. Can you distinguish whether this is truly benign traffic, or uncover the covert message buried within the noise?

Flag Format:
`hackzero{}`

## Files

- [Silent_Signals_in_the_Noise.zip](./Silent_Signals_in_the_Noise.zip)

## Writeup

> ```Flag:```  `hackzero{5734l7h13r_7h4n_4p7$}`

---


The covert channel was in the APT.pcap stream to port 4444: 5,000 synthetic TCP packets carrying either AAAAAAAAAA or BBBBBBBBBBB. 

Interpreting 10-byte A payloads as 0 and 11-byte B payloads as 1, then grouping into bytes, produced the Base64 prefix aGFja3plcm97NTczNGw3aDEzcl83aDRuXzRwNyR9Cg==, which decodes to the flag above.



The final workflow I followed was..

1. Extracting ZIP.
2. Identifying only artifact: APT.pcap.
3. Triage the visible traffic and hosts.

then I Notice abnormal concentration on TCP port 4444.
Dumped those packets only.
Observeing fake standalone packets with only two payload forms.
Maping 10-byte A payload to 0, 11-byte B payload to 1.
Packing bits into bytes.
Read the base64

Decoding it got the flag..

## Author

ret2.libc
