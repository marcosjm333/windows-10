#ifndef NW_BASE_H
#define NW_BASE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if !defined(__x86_64__) && !defined(_M_X64)
#error This foundation requires x86-64
#endif
_Static_assert(sizeof(void *) == 8, "64-bit pointers required");
#if defined(NW_HOST) && defined(_WIN32)
#define NW_API __declspec(dllexport)
#elif defined(NW_HOST)
#define NW_API __attribute__((visibility("default")))
#else
#define NW_API
#endif
#define NW_MS_ABI __attribute__((ms_abi))
#define NW_PAGE_SIZE UINT64_C(4096)
#define NW_RUNTIME UINT64_C(0x8000000000000000)
#define NW_MEMORY_WB UINT64_C(8)
#define NW_MEMORY_PROTECTED (UINT64_C(0x1000) | UINT64_C(0x2000) | UINT64_C(0x8000) | UINT64_C(0x20000))

typedef enum {
    NW_OK, NW_INVALID, NW_RANGE, NW_CAPACITY, NW_CORRUPT,
    NW_EXHAUSTED, NW_STALE, NW_OVERFLOW
} NwStatus;

void *memcpy(void *restrict dst, const void *restrict src, size_t n);
void *memmove(void *dst, const void *src, size_t n);
void *memset(void *dst, int value, size_t n);
int memcmp(const void *left, const void *right, size_t n);

static inline void nw_pause(void) { __asm__ volatile("pause"); }
static inline bool nw_add_u64(uint64_t a, uint64_t b, uint64_t *out) {
    if (b > UINT64_MAX - a) return false;
    *out = a + b;
    return true;
}
#endif
