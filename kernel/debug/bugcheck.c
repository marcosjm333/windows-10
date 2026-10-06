#include "arch/x64.h"
#include "internal/debug.h"

NwCrashRecord nw_crash_record;
static uint32_t claimed;

static void capture(uint64_t code, uint64_t a, uint64_t b) {
    nw_crash_record.version = 1;
    nw_crash_record.size = sizeof(nw_crash_record);
    nw_crash_record.code = code;
    nw_crash_record.parameters[0] = a;
    nw_crash_record.parameters[1] = b;
    __asm__ volatile("mov %%cr0, %0" : "=r"(nw_crash_record.cr0));
    __asm__ volatile("mov %%cr2, %0" : "=r"(nw_crash_record.cr2));
    __asm__ volatile("mov %%cr3, %0" : "=r"(nw_crash_record.cr3));
    __asm__ volatile("mov %%cr4, %0" : "=r"(nw_crash_record.cr4));
    __asm__ volatile("mov %%rsp, %0" : "=r"(nw_crash_record.rsp));
    __asm__ volatile("pushfq; popq %0" : "=r"(nw_crash_record.rflags));
    nw_crash_record.valid_fields = 1; /* control registers; optional groups follow */
}
_Noreturn void nw_bugcheck(uint64_t code, uint64_t a, uint64_t b) {
    nw_cli();
    if (__atomic_exchange_n(&claimed, 1, __ATOMIC_ACQ_REL) == 0) {
        capture(code, a, b);
        nw_crash_record.rip = (uintptr_t)__builtin_return_address(0);
        nw_log(NW_BUGCHECK, NW_FATAL, "BUGCHECK", code, a);
        nw_log(NW_BUGCHECK, NW_FATAL, "CONTEXT", nw_crash_record.rip, nw_crash_record.cr2);
    }
    nw_halt();
}
_Noreturn void nw_exception(const uint64_t *frame) {
    nw_cli();
    if (__atomic_exchange_n(&claimed, 1, __ATOMIC_ACQ_REL) == 0) {
        capture(UINT64_C(0x100) + frame[15], frame[16], frame[17]);
        for (size_t i = 0; i < 15; ++i) nw_crash_record.gpr[i] = frame[i];
        nw_crash_record.rip = frame[17];
        nw_crash_record.rflags = frame[19];
        nw_crash_record.rsp = frame[20];
        nw_crash_record.valid_fields |= 2;
        nw_log(NW_BUGCHECK, NW_FATAL, "EXCEPTION", frame[15], frame[16]);
        nw_log(NW_BUGCHECK, NW_FATAL, "CONTEXT", frame[17], nw_crash_record.cr2);
    }
    nw_halt();
}
