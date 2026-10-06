#include "internal/boot.h"

uint64_t nw_boot_exit(NwBootTransaction *t) {
    if (t == NULL || t->get_map == NULL || t->exit_boot == NULL ||
        t->buffer == NULL || t->capacity == 0 || t->exit_attempted || t->exited)
        return NW_EFI_INVALID;
    uint64_t status = NW_EFI_INVALID;
    for (uint32_t attempt = 0; attempt < 4; ++attempt) {
        size_t key = 0;
        t->length = t->capacity;
        t->stride = 0;
        t->version = 0;
        status = t->get_map(&t->length, t->buffer, &key, &t->stride, &t->version);
        if (status != 0) return status;
        if (t->length == 0 || t->length > t->capacity || t->stride < 40 ||
            t->stride % 8 != 0 || t->length % t->stride != 0 || t->version != 1)
            return NW_EFI_INVALID;
        t->exit_attempted = true;
        ++t->attempts;
        status = t->exit_boot(t->image, key);
        if (status == 0) { t->exited = true; return 0; }
        if (status != NW_EFI_INVALID) return status;
    }
    return status;
}
