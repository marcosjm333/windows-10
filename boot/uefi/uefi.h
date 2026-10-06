#ifndef NW_UEFI_H
#define NW_UEFI_H
#include "internal/boot.h"

typedef struct { uint64_t signature; uint32_t revision, size, crc32, reserved; } EfiHeader;
typedef uint64_t EfiStatus;
typedef EfiStatus (*EfiAllocatePages)(uint32_t, uint32_t, size_t, uint64_t *);
typedef EfiStatus (*EfiFreePages)(uint64_t, size_t);
typedef EfiStatus (*EfiAllocatePool)(uint32_t, size_t, void **);
typedef EfiStatus (*EfiFreePool)(void *);
/* Unused slots are data pointers solely to preserve the public table layout. */
typedef struct {
    EfiHeader header;
    void *raise_tpl, *restore_tpl;
    EfiAllocatePages allocate_pages;
    EfiFreePages free_pages;
    NwGetMap get_memory_map;
    EfiAllocatePool allocate_pool;
    EfiFreePool free_pool;
    void *create_event, *set_timer, *wait_for_event, *signal_event, *close_event;
    void *check_event, *install_protocol, *reinstall_protocol, *uninstall_protocol;
    void *handle_protocol, *reserved, *register_notify, *locate_handle;
    void *locate_device_path, *install_table, *load_image, *start_image, *exit_image;
    void *unload_image;
    NwExitBoot exit_boot_services;
} EfiBootServices;
typedef struct {
    EfiHeader header;
    void *vendor;
    uint32_t firmware_revision, pad;
    void *console_in_handle, *console_in, *console_out_handle, *console_out;
    void *stderr_handle, *stderr_interface, *runtime_services;
    EfiBootServices *boot_services;
    size_t table_count;
    void *tables;
} EfiSystemTable;
_Static_assert(sizeof(EfiHeader) == 24, "UEFI table header");
_Static_assert(offsetof(EfiBootServices, get_memory_map) == 56, "UEFI GetMemoryMap");
_Static_assert(offsetof(EfiBootServices, exit_boot_services) == 232, "UEFI ExitBootServices");
_Static_assert(offsetof(EfiSystemTable, boot_services) == 96, "UEFI system table");
#endif
