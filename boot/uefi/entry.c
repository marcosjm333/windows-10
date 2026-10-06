#include "uefi.h"
#include "arch/x64.h"
#include "internal/debug.h"

static _Alignas(16) unsigned char kernel_stack[65536];
static NwMemoryRange scratch[NW_MAP_CAPACITY];
static NwBootInfo boot_info;

EfiStatus efi_main(void *image, EfiSystemTable *system) {
    if (system == NULL || system->header.signature != UINT64_C(0x5453595320494249) ||
        system->header.size < sizeof(EfiSystemTable) || system->boot_services == NULL)
        return NW_EFI_INVALID;
    EfiBootServices *bs = system->boot_services;
    if (bs->header.signature != UINT64_C(0x56524553544f4f42) ||
        bs->header.size < sizeof(EfiBootServices)) return NW_EFI_INVALID;
    /* Provision an explicit bounded map buffer; never allocate during exit retries. */
    size_t capacity = 256 * 1024;
    void *map = NULL;
    EfiStatus status = bs->allocate_pool(2, capacity, &map); /* EfiLoaderData */
    if (status != 0) return status;
    size_t length = capacity, key = 0, stride = 0, count = 0;
    uint32_t version = 0;
    status = bs->get_memory_map(&length, map, &key, &stride, &version);
    if (status != 0) { (void)bs->free_pool(map); return status; }
    NwStatus parsed = nw_map_parse(map, length, stride, version, scratch, NW_MAP_CAPACITY, &count);
    if (parsed != NW_OK) { (void)bs->free_pool(map); return NW_EFI_INVALID; }
    size_t pages = 0;
    for (size_t i = 0; i < count; ++i) {
        if (!nw_range_usable(&scratch[i])) continue;
        if (scratch[i].pages > SIZE_MAX - pages) {
            (void)bs->free_pool(map); return NW_EFI_INVALID;
        }
        pages += (size_t)scratch[i].pages;
    }
    if (pages == 0 || pages > (SIZE_MAX - 4095) / sizeof(NwPfn)) {
        (void)bs->free_pool(map); return NW_EFI_INVALID;
    }
    size_t backing_pages = (pages * sizeof(NwPfn) + 4095) / 4096;
    uint64_t backing = 0;
    status = bs->allocate_pages(0, 2, backing_pages, &backing);
    if (status != 0) { (void)bs->free_pool(map); return status; }
    NwBootTransaction transaction = {0};
    transaction.get_map = bs->get_memory_map;
    transaction.exit_boot = bs->exit_boot_services;
    transaction.image = image;
    transaction.buffer = map;
    transaction.capacity = capacity;
    status = nw_boot_exit(&transaction);
    if (status != 0) {
        if (!transaction.exit_attempted) {
            (void)bs->free_pages(backing, backing_pages);
            (void)bs->free_pool(map);
            return status;
        }
        nw_cli(); nw_serial_init();
        nw_bugcheck(1, status, transaction.attempts);
    }
    nw_cli();
    boot_info = (NwBootInfo){NW_BOOT_VERSION, sizeof(NwBootInfo), map,
        transaction.length, transaction.stride, transaction.version, 0,
        (NwPfn *)(uintptr_t)backing, pages};
    nw_enter_kernel(&boot_info, kernel_stack + sizeof(kernel_stack));
}
