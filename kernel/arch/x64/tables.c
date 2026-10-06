#include "arch/x64.h"
#include "internal/debug.h"

typedef struct __attribute__((packed)) {
    uint32_t reserved0;
    uint64_t rsp[3], reserved1, ist[7], reserved2;
    uint16_t reserved3, iomap;
} NwTss;
typedef struct __attribute__((packed)) {
    uint16_t low, selector;
    uint8_t ist, attributes;
    uint16_t middle;
    uint32_t high, reserved;
} NwIdtGate;
typedef struct __attribute__((packed)) { uint16_t limit; uint64_t base; } NwDescriptor;
_Static_assert(sizeof(NwTss) == 104, "x64 TSS layout");
_Static_assert(offsetof(NwTss, ist) == 36, "x64 IST offset");
_Static_assert(sizeof(NwIdtGate) == 16, "x64 IDT layout");
static _Alignas(16) NwTss tss;
static _Alignas(16) NwIdtGate idt[256];
static _Alignas(16) uint64_t gdt[5];
static _Alignas(16) unsigned char emergency_stacks[3][16384];
extern const uintptr_t nw_isr_table[32];
extern void nw_isr_unexpected(void);

void nw_cpu_init(void) {
    nw_cli();
    memset(&tss, 0, sizeof(tss));
    uintptr_t rsp;
    __asm__ volatile("mov %%rsp, %0" : "=r"(rsp));
    tss.rsp[0] = rsp;
    for (size_t i = 0; i < 3; ++i)
        tss.ist[i] = (uintptr_t)(emergency_stacks[i] + sizeof(emergency_stacks[i]));
    tss.iomap = sizeof(tss);
    gdt[0] = 0;
    gdt[1] = UINT64_C(0x00af9a000000ffff);
    gdt[2] = UINT64_C(0x00cf92000000ffff);
    uint64_t base = (uintptr_t)&tss;
    gdt[3] = (sizeof(tss) - 1) | ((base & 0xffffff) << 16) |
             (UINT64_C(0x89) << 40) | (((base >> 24) & 0xff) << 56);
    gdt[4] = base >> 32;
    NwDescriptor gdtr = {sizeof(gdt) - 1, (uintptr_t)gdt};
    nw_load_gdt(&gdtr);
    for (size_t i = 0; i < 256; ++i) {
        uintptr_t address = i < 32 ? nw_isr_table[i] : (uintptr_t)nw_isr_unexpected;
        uint8_t ist = i == 8 ? 1 : (i == 2 ? 2 : (i == 18 ? 3 : 0));
        idt[i] = (NwIdtGate){(uint16_t)address, 8, ist, 0x8e,
                            (uint16_t)(address >> 16), (uint32_t)(address >> 32), 0};
    }
    NwDescriptor idtr = {sizeof(idt) - 1, (uintptr_t)idt};
    __asm__ volatile("lidt %0" : : "m"(idtr) : "memory");
    nw_log(NW_CPU, NW_INFO, "TABLES_READY", 256, 3);
}
