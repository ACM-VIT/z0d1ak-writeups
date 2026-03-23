# Private Binary

| Field      | Value |
|------------|-------|
| Category   | RE |
| Points     | 100 |
| Solves     | 248 |
| Tags       | RE, Crypto |

## Description

I managed to exfiltrate a highly classified, encrypted executable, but no tool I throw at it can parse it. It
doesn't even have an ELF header!

Fortunately, I also managed to exfiltrate the custom Linux Kernel Module (`loader.ko`) that the target system
uses to execute these files.

How does the executable run without an ELF header? Does the kernel module have something to do with it?


Author: mrdebator

## Files

- [loader.ko](./loader.ko)
- [flag.enc](./flag.enc)

## Writeup

### Flag

```

```

### Executive Summary


### Vulnerability Analysis


### Exploit Strategy


### Implementation


### Execution & Results


