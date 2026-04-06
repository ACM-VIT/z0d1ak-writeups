# Thread 0

| Field      | Value |
|------------|-------|
| Category   | Reversing |
| Points     | 250 |
| Solves     | 45 |

## Description

The program starts. You open the binary. You set your breakpoint. You already missed it.

## Files

- [thread_0.zip](./thread_0.zip)

## Writeup

> ```Flag:```  `hackzero{T15_C411B4CK_M4S73R}`

## Challenge Information
- **CTF Name:** HackZero 2026
- **Challenge Name:** Thread 0
- **Category:** Reversing
- **Points:** 250
- **Author:** @Niazi
- **Solved By:** ret2.libc

This was a very nice “you missed it already” style RE challenge, i.e., which means the real logic happens fast and it tries to push me into wrong debugging habits.


I saw it was a 64-bit Windows PE binary. Since I was on Kali vm, I ran it with Wine.

```bash
wine thread_0.exe
wine thread_0.exe test
```

Output:

```text
no arg -> Usage: challenge.exe <password>
wrong arg -> [-] Wrong.
```

That already told me input is CLI-based, i.e., which means password comes as argv, not scanf.

Then I did quick string recon:

```bash
strings -n 6 thread_0.exe | grep -Ei "Usage|Wrong|password|flag"
```

I found key strings, so I moved to static reversing (best for this one). I used Radare2, and I also used Python helpers (pefile + capstone) to speed up disassembly reading.

```bash
r2 -A thread_0.exe
```

Inside r2 I searched strings and xrefs:

```text
iz~Wrong
iz~Usage
axt @ <address_of_wrong_string>
axt @ <address_of_usage_string>
pdf @ <xref_function_addr>
```

From there, I landed in the main check function.
Super nice author trick: it checks password length first (0x10), i.e., which means exactly 16 bytes, then validates each byte with bit operations:

- xor
- rol/ror (rotate left/right)
- multiply by 23 (done as x*3, <<3, -x, i.e., which means final x*23)
- compare with constant

So each byte had pattern like:

```text
t = byte[i]
t = transform(t)   # xor + rol/ror (+ one not)
if (23 * t) & 0xff != CONST: fail
```

I inverted each step manually (reverse order), recovered all 16 characters, and got:

```text
I USE ARCH BTW!!
```

Then I verified it...

```bash
wine thread_0.exe "I USE ARCH BTW!!"
```

Output:

```text
[+] hackzero{T15_C411B4CK_M4S73R}
```

## Author

ret2.libc
