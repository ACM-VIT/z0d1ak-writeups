# An Alien Communication

| Field      | Value |
|------------|-------|
| Category   | Forensics |
| Points     | 150 |
| Solves     | 64 |

## Description

We intercepted what appears to be an alien communication channel. At first glance, it’s just a flood of normal-looking network noise - but something intelligent is hiding beneath it. The signal is masked using evasive techniques, blending seamlessly into the traffic to avoid detection. Somewhere in this chaos, a piece of data is being transmitted. Find it.

Flag Format:
`hackzero{}`

## Files

- [AnAlienCommunication.zip](./AnAlienCommunication.zip)

## Writeup

> ```Flag:```  `hackzero{1_l0v3_br41nfuck!}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** An Alien Communication
- **Category:** Forensics
- **Points:** 150
- **Author:** @Snehil(Mr0x00)
- **Solved By:** ret2.libc


This was a very nice challenge because it had multiple noisy channels, and only one channel had the real secret.

## Challenge

We got one file - `captured_for2.pcapng`
Flag format: `hackzero{...}`

## My Approach (Kali Linux)

Upon unziping it,

   I got one main file:
   - `captured_for2.pcapng` (network capture)

1. **recon of the capture**

  used wireshark for recon

   I saw mixed traffic, i.e. TCP/UDP/ICMP, which means many channels were present.

2. **Found suspicious traffic**

   I again my vm started to hang, I used cmd based network packet anaysis tool and checked HTTP-like payloads inside packets:

   - `tshark -r captured_for2.pcapng -Y 'tcp contains "Host: site.local"' -T fields -e frame.number -e ip.src -e ip.dst -e tcp.payload`
   - `tshark -r captured_for2.pcapng -Y 'udp contains "GET /" and udp contains "Host:"' -T fields -e frame.number -e ip.src -e ip.dst -e data.data`
   - `tshark -r captured_for2.pcapng -Y 'icmp' -T fields -e frame.number -e ip.src -e ip.dst -e icmp.seq -e data.data`

   I found:
   - `GET /pageNN` to `site.local` (TCP)
   - fake `GET /NN` to big domains (UDP)
   - ICMP echo packets to `10.10.5.5`

   The ICMP stream looked like exfiltration, i.e. hidden file transfer, which means I focused there.

4. **Rebuilding hidden ZIP from ICMP payload**

   I extracted ICMP payloads and reconstructed the ZIP.

   I used Python + Scapy: (tried manually since I study python, but couldn't do it, was getting errors, prettry programmers worry, lol. used ai to draft it, logical prompt was given and asked it to do what exactly is required.)

   ```python
   python3 - << 'PY'
   from scapy.all import rdpcap, IP, ICMP, Raw
   import itertools

   pcap = "captured_for2.pcapng"
   outf = "exfil.zip"

   pkts = rdpcap(pcap)
   payloads = []
   for p in pkts:
       if IP in p and ICMP in p and Raw in p:
           if p[IP].src == "10.0.2.15" and p[IP].dst == "10.10.5.5" and p[ICMP].type == 8:
               d = bytes(p[Raw].load)
               if d not in payloads:
                   payloads.append(d)

   zipdata = None
   for a, b in itertools.permutations(payloads, 2):
       c = a + b
       if c.startswith(b"PK\x03\x04") and b"PK\x05\x06" in c:
           zipdata = c
           break

   open(outf, "wb").write(zipdata)
   print("[+] wrote", outf, "size:", len(zipdata))
   PY
   ```

   Output ZIP was : `exfil.zip`

5. **Inspecting ZIP**
   - `unzip -l exfil.zip`
   - `zipinfo -v exfil.zip`

   I saw:
   - `flag/`
   - `flag/flag.txt` (encrypted with ZipCrypto)

   So password was needed.

6. **Finding hidden password in raw pcap bytes**

   This was the headace situation, tried j2h and then tried to find pass using rocku, but all -ve, so then thought and found that password was hidden in raw bytes, not obvious decoded stream.

   - `strings -a captured_for2.pcapng | grep -i 'search?q=\|supersecure'`

   I found:
   - `GET /search?q=SuperSecurePass! HTTP/1.1`

   So password = `SuperSecurePass!`

7. **Extract final flag**
   - `7z x exfil.zip -p'SuperSecurePass!' -o./out`
   - `cat out/flag/flag.txt`

   Flag:
   - `hackzero{1_l0v3_br41nfuck!}`

## Final Flag

`hackzero{1_l0v3_br41nfuck!}`

## Author

ret2.libc
