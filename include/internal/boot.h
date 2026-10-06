#ifndef NW_BOOT_H
#define NW_BOOT_H
#include "internal/memory.h"
#define NW_BOOT_VERSION 1u
#define NW_MAP_CAPACITY 1024u
typedef struct {
    uint32_t version, size;
    const void *map;
    size_t map_size, descriptor_size;
    uint32_t descriptor_version, reserved;
    NwPfn *pfn_storage;
    size_t pfn_capacity;
} NwBootInfo;
_Noreturn void nw_kernel_entry(const NwBootInfo *info);
_Noreturn void nw_enter_kernel(const NwBootInfo *info, void *stack_top);

/* Firmware callbacks preserve EFI_STATUS. The transaction is separately tested. */
typedef uint64_t (*NwGetMap)(size_t *, void *, size_t *, size_t *, uint32_t *);
typedef uint64_t (*NwExitBoot)(void *, size_t);
typedef struct {
    NwGetMap get_map;
    NwExitBoot exit_boot;
    void *image;
    void *buffer;
    size_t capacity;
    size_t length, stride;
    uint32_t version, attempts;
    bool exit_attempted, exited;
} NwBootTransaction;
#define NW_EFI_ERROR (UINT64_C(1) << 63)
#define NW_EFI_INVALID (NW_EFI_ERROR | 2)
#define NW_EFI_BUFFER_SMALL (NW_EFI_ERROR | 5)
NW_API uint64_t nw_boot_exit(NwBootTransaction *transaction);
#endif
