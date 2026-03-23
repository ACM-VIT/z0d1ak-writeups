# Goodbye libc

| Field      | Value |
|------------|-------|
| Category   | pwn |
| Points     | 80 |
| Solves     | 111 |

## Description

<p>Author: <code>FlamePyromancer</code></p><p>After extensive research, I learned that many binary exploitation methods involve hijacking standard C library functions. My friends told me I should employ "secure coding practices" due to "flaws" in my programs, so hopefully writing my own libc is good enough!</p>

## Files

- [goodbye-libc.tar.gz](./goodbye-libc.tar.gz)

## Writeup

### Flag

```
gigem{flamepyromancer_didnt_change_the_default_flag}
```

### Executive Summary

The source code gives us the vulnerability right up front: `input_index()` parses decimal input into a signed 32-bit `int` with no overflow protection. That means huge decimal numbers wrap around and end up in the allowed range. From there, we get negative array indices that `WRITE_NUM` doesn't validate.

So we have an out-of-bounds read/write primitive on the main stack frame. We leak the original stack pointer and a code pointer, then reuse `WRITE_NUM` to hijack the return address and redirect execution to `read@plt` for staged payloads.

The real breakthrough was forging a synthetic `PRINT_NUM` stack frame to walk up into the process's `auxv` and leak `AT_BASE`, which tells us the base of `ld-linux-x86-64.so.2`. With that, we can find real gadgets under ASLR. We use those gadgets to `execve("/bin/sh")` and cat the flag.

### Vulnerability Analysis

The source gives us the vulnerable function directly. In `input_index()`:

```c
int choice = 0;
for (int i = 0; i < 16; ++i) {
  if (input[i] >= '0' && input[i] <= '9') {
    choice = 10*choice + (input[i]-'0');
  } else {
    break;
  }
}

if (choice <= 3 && choice >= -2) {
  return choice-1;
} else {
  print("Invalid index!\n\n");
  return -1;
}
```

The issue: `choice` is a signed 32-bit `int`, and we control the input string. No overflow checks. So we can send massive decimal values that wrap around:

- `4294967294` wraps to `-2` → returns `-3`
- `4294967295` wraps to `-1` → returns `-2`
- `4294967296` wraps to `0` → returns `-1`

Most menu cases validate the result, but `WRITE_NUM` doesn't:

```c
case WRITE_NUM:
  print("Select index to write to [1-3]: ");
  index = input_index();
  write_num(&nums[index]);
  break;
```

Negative indices into the stack array give us out-of-bounds access. Since the array lives on `_start`'s stack frame, we get two immediate primitives:

1. `PRINT_NUM` with negative index → leak qwords above `nums`
2. `WRITE_NUM` with negative index → write qwords above `nums`

The especially useful bit: during the `write_num()` call, the saved return address lives at a predictable offset. That gives us `WRITE_NUM(-2)` as a direct RIP control when `write_num()` returns.

### Exploit Strategy

We break this into five stages.

#### 1. Leak the original stack and PIE base

We use the negative indices immediately:

- `PRINT_NUM(-3)` leaks the saved `_start` `rbp`
- `PRINT_NUM(-2)` leaks a code pointer

From the second leak, we compute:
```text
pie_base = leak - 0x1CBD
```

That's our starting foothold.

#### 2. Hijack the return address and stage a `read`

We use `WRITE_NUM(-2)` to overwrite `write_num()`'s return address with `read@plt`. Now after the numeric parsing completes, we get a fresh `read()` call with controlled arguments.

The stack geometry of that staged read:
- buffer starts at `orig_rbp - 0xbc`
- the `read` call's saved `rbp` lands at buffer offset `0x74`
- the return address lands at buffer offset `0x7c`

So we can control both `rbp` and `rip` by crafting the payload.

#### 3. Early attempts that didn't work

Our first thought was to rebase `rbp` into `.got` and leak the custom libc. That _did_ work for leaks, but writing back to GOT on remote crashed immediately. SROP via vsyscall looked promising but the host died on every syscall attempt. Dead ends, both of them.

#### 4. Real breakthrough: forge a `PRINT_NUM` frame and read `auxv`

Instead of pivoting off the stack, we stayed on the real stack. We set the staged read's saved `rbp` to `orig_rbp - 0x10` and returned into the `PRINT_NUM` case block. We also crafted the forged `index` variable.

Now `PRINT_NUM` reads above the original `nums` array, which means we can walk the early process stack:
- `argc`
- `argv[]`
- `envp[]`
- `auxv[]`

We spotted `AT_SYSINFO_EHDR = 33` and the vDSO right after to confirm we were in the right place. We kept scanning for `AT_BASE = 7` and read its value. That leaked the loader base.

One leak solved the gadget problem completely.

#### 5. Final ROP chain into `execve("/bin/sh")`

With the loader base, we found:
- `pop rdi ; ret = ld + 0x324F`
- `pop rsi ; ret = ld + 0x3B6A`
- `pop rax ; pop rdx ; pop rbx ; ret = ld + 0x1AB9E`
- `syscall ; ret = ld + 0x12C55`

We staged one more read to place `"/bin/sh\x00"`, an argv pointer, and the ROP chain on the stack. Then we jumped at it and got a shell.

### Implementation

The challenge doesn't list an explicit remote in the brief, but the bundled template inside the archive gives us the endpoint:

```python
io = remote("streams.tamuctf.com", 443, ssl=True, sni="goodbye-libc")
```

Our exploit flow is:

```python
stack, pie = leak_stack_and_pie(io)
ld = leak_ld_base(io, stack, pie)
spawn_shell(io, stack, pie, ld)
io.sendline(b"echo __BEGIN__; /bin/cat /flag* 2>/dev/null; echo __END__")
```

First helper gets the stack and code:

```python
def leak_stack_and_pie(io):
    stack = print_idx(io, -3)
    pie = print_idx(io, -2) - 0x1CBD
    return stack, pie
```

Then we reuse the return-address overwrite to jump into a synthetic `PRINT_NUM` frame and read `AT_BASE` from auxv. After that, we build the final ROP chain and execute it.

We wrapped everything in a retry loop because the synthetic auxv leak works reliably but isn't perfectly deterministic on every connection.

### Results

The successful run gave us:

```text
__BEGIN__
gigem{flamepyromancer_didnt_change_the_default_flag}
__END__
```

### Artifacts

- [artifacts/goodbye_libc_exploit.py](./artifacts/goodbye_libc_exploit.py): final pwntools solve script
- [artifacts/goodbye_libc_run.txt](./artifacts/goodbye_libc_run.txt): successful exploit transcript
- [artifacts/goodbye_libc_flag.txt](./artifacts/goodbye_libc_flag.txt): recovered flag
- [artifacts/goodbye-libc.c](./artifacts/goodbye-libc.c): main challenge source used during reversing
- [artifacts/bye-libc.c](./artifacts/bye-libc.c): custom libc source used to reason about syscalls and gadget quality
