/* Hosted harness only: the kernel remains CRT-free. */
#include <stdlib.h>
#include "internal/memory.h"
int main(void) {
    NwMemoryRange ranges[2] = {{0x100000, 512, 8, 7, 0}, {0x100000000, 512, 8, 7, 0}};
    NwPfn *storage = calloc(1024, sizeof(*storage));
    if (!storage) return 1;
    NwPfnDatabase db;
    if (nw_pfn_init(&db, storage, 1024, ranges, 2) != NW_OK) return 2;
    NwFrame frames[1024];
    for (size_t i = 0; i < 1024; ++i)
        if (nw_frame_alloc(&db, &frames[i]) != NW_OK) return 3;
    for (size_t i = 0; i < 1024; ++i) {
        if (nw_frame_retain(&db, frames[i]) != NW_OK) return 4;
        if (nw_frame_release(&db, frames[i]) != NW_OK) return 5;
        if (nw_frame_release(&db, frames[i]) != NW_OK) return 6;
        if (nw_frame_release(&db, frames[i]) != NW_STALE) return 7;
    }
    if (nw_pfn_check(&db) != NW_OK) return 8;
    unsigned char fuzz[256];
    uint32_t state = 0x51f15e;
    for (unsigned test = 0; test < 50000; ++test) {
        for (size_t i = 0; i < sizeof(fuzz); ++i) {
            state ^= state << 13; state ^= state >> 17; state ^= state << 5;
            fuzz[i] = (unsigned char)state;
        }
        size_t count = 0;
        (void)nw_map_parse(fuzz, test % sizeof(fuzz), 48, 1, ranges, 2, &count);
    }
    free(storage);
    return 0;
}
