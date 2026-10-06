#ifndef NW_MEMORY_H
#define NW_MEMORY_H
#include "internal/base.h"

typedef struct {
    uint64_t base, pages, attributes;
    uint32_t type, reserved;
} NwMemoryRange;

/* Output storage is scratch until success. Input must remain immutable and
 * must not overlap output. Count is set to zero on any failure. */
NW_API NwStatus nw_map_parse(const void *bytes, size_t length, size_t stride,
                            uint32_t version, NwMemoryRange *ranges,
                            size_t capacity, size_t *count);
NW_API bool nw_range_usable(const NwMemoryRange *range);

typedef struct { uint32_t next, serving; } NwTicketLock;
typedef struct {
    uint64_t physical, generation;
    uint32_t references, retired;
} NwPfn;
typedef struct { uint64_t physical, generation; } NwFrame;
typedef struct {
    NwTicketLock lock;
    NwPfn *entries;
    size_t count, free_count, cursor;
} NwPfnDatabase;

/* Initialize exactly once, before publication. Metadata outlives all callers.
 * No ISR/NMI use. Kernel callers mask interrupt/preemption reentry. */
NW_API NwStatus nw_pfn_init(NwPfnDatabase *db, NwPfn *storage, size_t capacity,
                          const NwMemoryRange *ranges, size_t range_count);
NW_API NwStatus nw_frame_alloc(NwPfnDatabase *db, NwFrame *frame);
NW_API NwStatus nw_frame_retain(NwPfnDatabase *db, NwFrame frame);
NW_API NwStatus nw_frame_release(NwPfnDatabase *db, NwFrame frame);
NW_API NwStatus nw_pfn_check(NwPfnDatabase *db);
NW_API size_t nw_pfn_free_count(NwPfnDatabase *db);
#endif
