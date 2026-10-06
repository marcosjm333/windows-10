#include "internal/memory.h"

static void lock_db(NwPfnDatabase *db) {
    uint32_t ticket = __atomic_fetch_add(&db->lock.next, 1u, __ATOMIC_RELAXED);
    while (__atomic_load_n(&db->lock.serving, __ATOMIC_ACQUIRE) != ticket)
        nw_pause();
}
static void unlock_db(NwPfnDatabase *db) {
    (void)__atomic_fetch_add(&db->lock.serving, 1u, __ATOMIC_RELEASE);
}

NwStatus nw_pfn_init(NwPfnDatabase *db, NwPfn *storage, size_t capacity,
                    const NwMemoryRange *ranges, size_t range_count) {
    if (db == NULL || storage == NULL || ranges == NULL || range_count == 0 ||
        (uintptr_t)storage % _Alignof(NwPfn) != 0) return NW_INVALID;
    size_t needed = 0;
    uint64_t previous_end = 0;
    for (size_t i = 0; i < range_count; ++i) {
        const NwMemoryRange *r = &ranges[i];
        if ((r->base & (NW_PAGE_SIZE - 1)) != 0 || r->pages == 0 ||
            r->pages > (UINT64_MAX - r->base) / NW_PAGE_SIZE ||
            r->base < previous_end) return NW_RANGE;
        previous_end = r->base + r->pages * NW_PAGE_SIZE;
        if (nw_range_usable(r)) {
            if (r->pages > SIZE_MAX - needed) return NW_OVERFLOW;
            needed += (size_t)r->pages;
        }
    }
    if (needed > capacity) return NW_CAPACITY;
    if (needed == 0) return NW_EXHAUSTED;
    size_t n = 0;
    for (size_t i = 0; i < range_count; ++i) {
        if (!nw_range_usable(&ranges[i])) continue;
        for (uint64_t page = 0; page < ranges[i].pages; ++page)
            storage[n++] = (NwPfn){ranges[i].base + page * NW_PAGE_SIZE, 0, 0, 0};
    }
    /* Publication belongs to caller; a failed init leaves db untouched. */
    *db = (NwPfnDatabase){{0, 0}, storage, needed, needed, 0};
    return NW_OK;
}

static NwPfn *lookup(NwPfnDatabase *db, NwFrame f) {
    size_t lo = 0, hi = db->count;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (db->entries[mid].physical < f.physical) lo = mid + 1;
        else hi = mid;
    }
    if (lo == db->count) return NULL;
    NwPfn *p = &db->entries[lo];
    if (p->physical != f.physical || p->generation != f.generation ||
        p->references == 0 || p->retired) return NULL;
    return p;
}

NwStatus nw_frame_alloc(NwPfnDatabase *db, NwFrame *frame) {
    if (db == NULL || frame == NULL || db->entries == NULL) return NW_INVALID;
    lock_db(db);
    for (size_t visited = 0; db->free_count != 0 && visited < db->count; ++visited) {
        size_t index = db->cursor;
        db->cursor = index + 1 == db->count ? 0 : index + 1;
        NwPfn *p = &db->entries[index];
        if (p->references != 0 || p->retired) continue;
        --db->free_count;
        if (p->generation == UINT64_MAX) {
            p->retired = 1;
            continue;
        }
        ++p->generation;
        p->references = 1;
        *frame = (NwFrame){p->physical, p->generation};
        unlock_db(db);
        return NW_OK;
    }
    unlock_db(db);
    return NW_EXHAUSTED;
}

NwStatus nw_frame_retain(NwPfnDatabase *db, NwFrame frame) {
    if (db == NULL || db->entries == NULL) return NW_INVALID;
    lock_db(db);
    NwPfn *p = lookup(db, frame);
    NwStatus status = NW_STALE;
    if (p != NULL) {
        if (p->references == UINT32_MAX) status = NW_OVERFLOW;
        else { ++p->references; status = NW_OK; }
    }
    unlock_db(db);
    return status;
}

NwStatus nw_frame_release(NwPfnDatabase *db, NwFrame frame) {
    if (db == NULL || db->entries == NULL) return NW_INVALID;
    lock_db(db);
    NwPfn *p = lookup(db, frame);
    NwStatus status = NW_STALE;
    if (p != NULL) {
        if (--p->references == 0) ++db->free_count;
        status = NW_OK;
    }
    unlock_db(db);
    return status;
}

size_t nw_pfn_free_count(NwPfnDatabase *db) {
    lock_db(db);
    size_t count = db->free_count;
    unlock_db(db);
    return count;
}

NwStatus nw_pfn_check(NwPfnDatabase *db) {
    if (db == NULL || db->entries == NULL || db->count == 0) return NW_INVALID;
    lock_db(db);
    size_t free_count = 0;
    NwStatus result = NW_OK;
    for (size_t i = 0; i < db->count; ++i) {
        NwPfn *p = &db->entries[i];
        if ((p->physical & (NW_PAGE_SIZE - 1)) != 0 ||
            (i > 0 && db->entries[i - 1].physical >= p->physical) ||
            (p->references != 0 && (p->generation == 0 || p->retired)) ||
            (p->retired && p->generation != UINT64_MAX)) result = NW_CORRUPT;
        if (p->references == 0 && !p->retired) ++free_count;
    }
    if (free_count != db->free_count || db->cursor >= db->count) result = NW_CORRUPT;
    unlock_db(db);
    return result;
}
