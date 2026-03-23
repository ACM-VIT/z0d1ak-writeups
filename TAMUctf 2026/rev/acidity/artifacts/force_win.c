#define _GNU_SOURCE
#include <link.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static uintptr_t g_base;

static int find_base_cb(struct dl_phdr_info *info, size_t size, void *data) {
    (void)size;
    (void)data;
    if (info->dlpi_name == NULL || info->dlpi_name[0] == '\0') {
        g_base = info->dlpi_addr;
        return 1;
    }
    return 0;
}

static void patch_bytes(void *dst, const unsigned char *src, size_t len) {
    size_t page = (size_t)sysconf(_SC_PAGESIZE);
    uintptr_t start = (uintptr_t)dst & ~(page - 1);
    mprotect((void *)start, page, PROT_READ | PROT_WRITE | PROT_EXEC);
    memcpy(dst, src, len);
    __builtin___clear_cache(dst, (unsigned char *)dst + len);
}

__attribute__((constructor)) static void init(void) {
    static const unsigned char nops[6] = {
        0x90, 0x90, 0x90, 0x90, 0x90, 0x90,
    };
    dl_iterate_phdr(find_base_cb, NULL);
    if (g_base == 0) {
        return;
    }
    patch_bytes((void *)(g_base + 0x1cbde), nops, sizeof(nops));
}
