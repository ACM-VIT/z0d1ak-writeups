# Routine Checks

| Field      | Value |
|------------|-------|
| Category   | Forensics |
| Points     | 50 |
| Solves     | 223 |

## Description

Routine system checks were performed on the city's communication network after reports of instability.

Operators sent brief messages between nodes to confirm everything was running smoothly.

Most of the exchanges are ordinary status updates, but one message stands out as... different.

> Author : Gopi

## Files

- [challenge.pcap](./challenge.pcap)

## Writeup

### Flag

```text
apoorvctf{b1ts_wh1sp3r_1n_th3_l0w3st_b1t}
```

### Executive Summary

The PCAP mostly contains routine localhost TCP status traffic. One stream is a clear outlier by size. Reassembling that stream reveals a slightly corrupted JPEG with a QR code decoy, and further steganography extraction from the same image reveals the real flag.

### Vulnerability Analysis

The challenge relies on layered hiding rather than protocol complexity:

- Network traffic is intentionally repetitive to hide one anomalous transfer.
- The suspicious payload is disguised as a damaged JPEG (first byte altered).
- The visible QR output is a decoy flag.
- Real content is embedded as hidden data inside the JPEG.

### Exploit Strategy

1. Triage capture and identify abnormal TCP stream by conversation statistics.
2. Reassemble payload from that stream.
3. Repair JPEG magic byte and inspect visible content.
4. Treat visible QR result as untrusted until verified.
5. Extract hidden file via stego tooling to obtain final message.

### Implementation

Useful commands:

```bash
# 1) Find outlier stream
tshark -r challenge.pcap -q -z conv,tcp

# 2) Reassemble stream payload
tshark -r challenge.pcap -Y "tcp.stream==1 && tcp.len>0" -T fields -e data | tr -d '\n' > stream1.hex
xxd -r -p stream1.hex > stream1.bin

# 3) Fix header and validate JPEG
cp stream1.bin stream1.jpg
printf '\xff' | dd of=stream1.jpg bs=1 seek=0 count=1 conv=notrunc

# 4) Extract hidden content
steghide extract -sf stream1.jpg -p '' -f
cat out
```

### Execution & Results

- The QR code decodes to a decoy value.
- `steghide` extraction with empty passphrase yields the real flag shown above.

