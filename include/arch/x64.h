#ifndef NW_X64_H
#define NW_X64_H
#include "internal/base.h"
static inline void nw_out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline uint8_t nw_in8(uint16_t port) {
    uint8_t value;
    __asm__ volatile("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}
static inline void nw_cli(void) { __asm__ volatile("cli" : : : "memory"); }
_Noreturn static inline void nw_halt(void) {
    nw_cli();
    for (;;) __asm__ volatile("hlt");
}
void nw_cpu_init(void);
void nw_load_gdt(const void *descriptor);
#endif
