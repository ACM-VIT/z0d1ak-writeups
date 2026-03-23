#define _GNU_SOURCE
#include <ctype.h>
#include <dlfcn.h>
#include <link.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

static uintptr_t g_base;
static unsigned char *script_bytes;
static size_t script_len;
static uint64_t frame_index;
static long speed_div = 100;
static int debug_script;
static int (*real_nanosleep_fn)(const struct timespec *, struct timespec *);
__attribute__((used)) void *resume_b06f;
__attribute__((used)) void *resume_cb90;
__attribute__((used)) void *resume_d986;
__attribute__((used)) void *resume_e9a4;

static int hex_nibble(int ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

static void parse_script_env(void) {
    const char *hex = getenv("ACID_SCRIPT_HEX");
    if (hex == NULL || *hex == '\0') {
        return;
    }

    size_t n = 0;
    for (const char *p = hex; *p; ++p) {
        if (!isspace((unsigned char)*p)) {
            ++n;
        }
    }
    if ((n & 1U) != 0) {
        return;
    }

    script_bytes = calloc(n / 2, 1);
    if (script_bytes == NULL) {
        return;
    }

    int hi = -1;
    size_t out = 0;
    for (const char *p = hex; *p; ++p) {
        if (isspace((unsigned char)*p)) {
            continue;
        }
        int v = hex_nibble((unsigned char)*p);
        if (v < 0) {
            free(script_bytes);
            script_bytes = NULL;
            script_len = 0;
            return;
        }
        if (hi < 0) {
            hi = v;
        } else {
            script_bytes[out++] = (unsigned char)((hi << 4) | v);
            hi = -1;
        }
    }
    script_len = out;
}

static int find_base_cb(struct dl_phdr_info *info, size_t size, void *data) {
    (void)size;
    (void)data;
    if (info->dlpi_name == NULL || info->dlpi_name[0] == '\0') {
        g_base = info->dlpi_addr;
        return 1;
    }
    return 0;
}

static void write_jump(void *dst, void *target, size_t patch_len) {
    unsigned char patch[16];
    patch[0] = 0x48;
    patch[1] = 0xB8;
    memcpy(&patch[2], &target, sizeof(target));
    patch[10] = 0xFF;
    patch[11] = 0xE0;
    for (size_t i = 12; i < patch_len && i < sizeof(patch); ++i) {
        patch[i] = 0x90;
    }
    memcpy(dst, patch, patch_len);
}

static void install_skip_hook(void *site, void *hook, size_t patch_len) {
    size_t page = (size_t)sysconf(_SC_PAGESIZE);
    uintptr_t start = (uintptr_t)site & ~(page - 1);
    mprotect((void *)start, page, PROT_READ | PROT_WRITE | PROT_EXEC);
    write_jump(site, hook, patch_len);
    __builtin___clear_cache(site, (unsigned char *)site + patch_len);
}

__attribute__((used)) uint32_t next_scripted_value(void) {
    uint32_t out = 0;
    if (script_bytes != NULL && frame_index < script_len) {
        out = script_bytes[frame_index];
    }
    if (debug_script && frame_index < 32) {
        char c = (out >= 32 && out <= 126) ? (char)out : '.';
        dprintf(2, "script frame=%llu input=0x%x '%c'\n",
                (unsigned long long)(frame_index + 1), out, c);
    }
    frame_index++;
    return out;
}

__attribute__((naked)) static void hook_b06f(void) {
    __asm__(
        "push %rax\n"
        "push %rcx\n"
        "push %rdx\n"
        "push %rsi\n"
        "push %rdi\n"
        "push %r8\n"
        "push %r9\n"
        "push %r10\n"
        "call next_scripted_value\n"
        "mov %eax, %ebp\n"
        "xor %r11d, %r11d\n"
        "pop %r10\n"
        "pop %r9\n"
        "pop %r8\n"
        "pop %rdi\n"
        "pop %rsi\n"
        "pop %rdx\n"
        "pop %rcx\n"
        "pop %rax\n"
        "mov resume_b06f@GOTPCREL(%rip), %rax\n"
        "mov (%rax), %rax\n"
        "jmp *%rax\n");
}

__attribute__((naked)) static void hook_cb90(void) {
    __asm__(
        "push %rax\n"
        "push %rcx\n"
        "push %rsi\n"
        "push %rdi\n"
        "push %r8\n"
        "push %r9\n"
        "push %r10\n"
        "push %rbp\n"
        "call next_scripted_value\n"
        "mov %eax, %edx\n"
        "xor %r11d, %r11d\n"
        "pop %rbp\n"
        "pop %r10\n"
        "pop %r9\n"
        "pop %r8\n"
        "pop %rdi\n"
        "pop %rsi\n"
        "pop %rcx\n"
        "pop %rax\n"
        "mov resume_cb90@GOTPCREL(%rip), %rax\n"
        "mov (%rax), %rax\n"
        "jmp *%rax\n");
}

__attribute__((naked)) static void hook_d986(void) {
    __asm__(
        "push %rax\n"
        "push %rcx\n"
        "push %rsi\n"
        "push %rdi\n"
        "push %r8\n"
        "push %r9\n"
        "push %r10\n"
        "push %rbp\n"
        "call next_scripted_value\n"
        "mov %eax, %edx\n"
        "xor %r11d, %r11d\n"
        "pop %rbp\n"
        "pop %r10\n"
        "pop %r9\n"
        "pop %r8\n"
        "pop %rdi\n"
        "pop %rsi\n"
        "pop %rcx\n"
        "pop %rax\n"
        "mov resume_d986@GOTPCREL(%rip), %rax\n"
        "mov (%rax), %rax\n"
        "jmp *%rax\n");
}

__attribute__((naked)) static void hook_e9a4(void) {
    __asm__(
        "push %rax\n"
        "push %rcx\n"
        "push %rsi\n"
        "push %rdi\n"
        "push %r8\n"
        "push %r9\n"
        "push %r10\n"
        "push %rbp\n"
        "call next_scripted_value\n"
        "mov %eax, %edx\n"
        "xor %r11d, %r11d\n"
        "pop %rbp\n"
        "pop %r10\n"
        "pop %r9\n"
        "pop %r8\n"
        "pop %rdi\n"
        "pop %rsi\n"
        "pop %rcx\n"
        "pop %rax\n"
        "mov resume_e9a4@GOTPCREL(%rip), %rax\n"
        "mov (%rax), %rax\n"
        "jmp *%rax\n");
}

int nanosleep(const struct timespec *req, struct timespec *rem) {
    (void)req;
    (void)rem;
    return 0;
}

__attribute__((constructor)) static void init(void) {
    const char *speed = getenv("ACID_SPEED_DIV");
    debug_script = getenv("ACID_DEBUG_SCRIPT") != NULL;
    if (speed != NULL && *speed != '\0') {
        char *end = NULL;
        long parsed = strtol(speed, &end, 10);
        if (end != speed && parsed > 0) {
            speed_div = parsed;
        }
    }
    parse_script_env();
    dl_iterate_phdr(find_base_cb, NULL);
    if (!g_base) {
        return;
    }
    resume_b06f = (void *)(g_base + 0xb07f);
    resume_cb90 = (void *)(g_base + 0xcba0);
    resume_d986 = (void *)(g_base + 0xd996);
    resume_e9a4 = (void *)(g_base + 0xe9b4);
    install_skip_hook((void *)(g_base + 0xb06f), hook_b06f, 16);
    install_skip_hook((void *)(g_base + 0xcb90), hook_cb90, 16);
    install_skip_hook((void *)(g_base + 0xd986), hook_d986, 16);
    install_skip_hook((void *)(g_base + 0xe9a4), hook_e9a4, 16);
}
