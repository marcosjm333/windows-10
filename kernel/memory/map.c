#include "internal/memory.h"

static uint64_t read64(const unsigned char *p) {
    uint64_t value;
    memcpy(&value, p, sizeof(value));
    return value;
}
static uint32_t read32(const unsigned char *p) {
    uint32_t value;
    memcpy(&value, p, sizeof(value));
    return value;
}

bool nw_range_usable(const NwMemoryRange *r) {
    return r->type == 7 && (r->attributes & NW_MEMORY_WB) != 0 &&
           (r->attributes & (NW_RUNTIME | NW_MEMORY_PROTECTED)) == 0;
}

NwStatus nw_map_parse(const void *bytes, size_t length, size_t stride,
                     uint32_t version, NwMemoryRange *out,
                     size_t capacity, size_t *count) {
    if (count == NULL) return NW_INVALID;
    *count = 0;
    if (bytes == NULL || out == NULL || version != 1 || stride < 40 ||
        stride % 8 != 0 || length == 0 || length % stride != 0)
        return NW_INVALID;
    size_t total = length / stride;
    if (total > capacity) return NW_CAPACITY;
    const unsigned char *raw = bytes;
    for (size_t i = 0; i < total; ++i) {
        const unsigned char *d = raw + i * stride;
        NwMemoryRange r = {read64(d + 8), read64(d + 24), read64(d + 32),
                           read32(d), 0};
        if ((r.base & (NW_PAGE_SIZE - 1)) != 0 || r.pages == 0 ||
            r.pages > (UINT64_MAX - r.base) / NW_PAGE_SIZE)
            return NW_RANGE;
        /* Insertion sort needs no allocation and accepts firmware ordering. */
        size_t j = i;
        while (j > 0 && out[j - 1].base > r.base) {
            out[j] = out[j - 1];
            --j;
        }
        out[j] = r;
    }
    for (size_t i = 1; i < total; ++i)
        if (out[i - 1].base + out[i - 1].pages * NW_PAGE_SIZE > out[i].base)
            return NW_CORRUPT;
    *count = total;
    return NW_OK;
}
