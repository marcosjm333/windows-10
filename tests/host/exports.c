#include "internal/debug.h"
#include "internal/memory.h"

/* A C -> assembly edge verifies compiler call placement as well as ctypes. */
NW_API uint64_t nw_abi_from_c(void) { return nw_abi_probe(1, 2, 3, 4, 5, 6); }
NW_API uint64_t nw_abi_nonvolatile(void) { return nw_abi_preserved(); }
typedef struct { uint64_t a, b, c; } NwAggregate;
NW_API NwAggregate nw_abi_aggregate(NwAggregate input, uint64_t add) {
    return (NwAggregate){input.a + add, input.b + add, input.c + add};
}

/* Host workers run this concurrently through ctypes, which releases its GIL.
 * Busy markers detect duplicate live ownership independently of PFN locks. */
NW_API uint32_t nw_pfn_stress(NwPfnDatabase *db, uint32_t *busy,
                              uint64_t base, uint32_t iterations) {
    for (uint32_t i = 0; i < iterations; ++i) {
        NwFrame f;
        NwStatus status = nw_frame_alloc(db, &f);
        if (status != NW_OK) return 1;
        size_t slot = (size_t)((f.physical - base) / NW_PAGE_SIZE);
        if (__atomic_exchange_n(&busy[slot], 1, __ATOMIC_ACQ_REL) != 0) return 2;
        if (nw_frame_retain(db, f) != NW_OK) return 3;
        if (nw_frame_release(db, f) != NW_OK) return 4;
        if (__atomic_exchange_n(&busy[slot], 0, __ATOMIC_ACQ_REL) != 1) return 5;
        if (nw_frame_release(db, f) != NW_OK) return 6;
    }
    return 0;
}
