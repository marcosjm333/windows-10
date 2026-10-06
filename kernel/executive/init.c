#include "internal/boot.h"
#include "internal/debug.h"
#include "arch/x64.h"

static NwMemoryRange ranges[NW_MAP_CAPACITY];
static NwPfnDatabase physical_memory;

_Noreturn void nw_kernel_entry(const NwBootInfo *info) {
    nw_serial_init();
    nw_log(NW_BOOT, NW_INFO, "KERNEL_ENTER", 1, 0);
    nw_cpu_init();
    if (info == NULL || info->version != NW_BOOT_VERSION || info->size != sizeof(*info))
        nw_bugcheck(2, 0, 0);
    size_t count = 0;
    NwStatus s = nw_map_parse(info->map, info->map_size, info->descriptor_size,
                            info->descriptor_version, ranges, NW_MAP_CAPACITY, &count);
    if (s != NW_OK) nw_bugcheck(3, (uint64_t)s, info->map_size);
    s = nw_pfn_init(&physical_memory, info->pfn_storage, info->pfn_capacity, ranges, count);
    if (s != NW_OK) nw_bugcheck(4, (uint64_t)s, count);
    nw_log(NW_PFN, NW_INFO, "PFN_READY", physical_memory.count, count);
    NwFrame frame;
    size_t initial = nw_pfn_free_count(&physical_memory);
    if (nw_frame_alloc(&physical_memory, &frame) != NW_OK) nw_bugcheck(5, 1, 0);
    /* The firmware's identity map remains pinned in this boot phase. Exercise
     * only a page for which this test holds a live PFN reference. */
    volatile uint64_t *page = (volatile uint64_t *)(uintptr_t)frame.physical;
    for (size_t i = 0; i < NW_PAGE_SIZE / sizeof(uint64_t); ++i)
        page[i] = UINT64_C(0xcafef00d12345678) ^ (uint64_t)i;
    for (size_t i = 0; i < NW_PAGE_SIZE / sizeof(uint64_t); ++i)
        if (page[i] != (UINT64_C(0xcafef00d12345678) ^ (uint64_t)i)) nw_bugcheck(5, 2, i);
    for (size_t i = 0; i < NW_PAGE_SIZE / sizeof(uint64_t); ++i) page[i] = 0;
    if (nw_frame_retain(&physical_memory, frame) != NW_OK ||
        nw_frame_release(&physical_memory, frame) != NW_OK ||
        nw_frame_release(&physical_memory, frame) != NW_OK ||
        nw_frame_release(&physical_memory, frame) != NW_STALE ||
        nw_pfn_free_count(&physical_memory) != initial ||
        nw_pfn_check(&physical_memory) != NW_OK) nw_bugcheck(5, 0, 0);
    nw_log(NW_MM, NW_INFO, "PFN_SELFTEST_PASS", initial, 0);
    if (nw_abi_probe(1, 2, 3, 4, 5, 6) != 91 || nw_abi_preserved() != 1)
        nw_bugcheck(6, 0, 0);
    nw_log(NW_CPU, NW_INFO, "ABI_SELFTEST_PASS", 6, 0);
#ifdef NW_TEST_EXCEPTION
    __asm__ volatile("ud2");
#endif
    nw_log(NW_BOOT, NW_INFO, "FOUNDATION_READY", 1, 0);
    /* No runnable threads exist. This terminal boot phase is not a scheduler. */
    nw_halt();
}
