#ifndef NW_DEBUG_H
#define NW_DEBUG_H
#include "internal/base.h"
typedef enum {
    NW_BOOT, NW_HAL, NW_CPU, NW_MM, NW_PFN, NW_VM, NW_SCHED, NW_PS,
    NW_OB, NW_IO, NW_PNP, NW_POWER, NW_SEC, NW_REG, NW_LDR, NW_PE,
    NW_DPC, NW_APC, NW_IRQ, NW_LOCK, NW_DRIVER, NW_BUGCHECK
} NwCategory;
typedef enum { NW_TRACE, NW_DEBUG, NW_INFO, NW_WARN, NW_ERROR, NW_FATAL } NwLevel;
typedef struct {
    uint32_t version, size;
    uint64_t code, parameters[4], cr0, cr2, cr3, cr4, rip, rsp, rflags;
    uint64_t gpr[15];
    uint64_t valid_fields;
} NwCrashRecord;
extern NwCrashRecord nw_crash_record;
void nw_serial_init(void);
void nw_log(NwCategory category, NwLevel level, const char *event, uint64_t a, uint64_t b);
_Noreturn void nw_bugcheck(uint64_t code, uint64_t a, uint64_t b);
_Noreturn void nw_exception(const uint64_t *frame);
NW_API uint64_t NW_MS_ABI nw_abi_probe(uint64_t a, uint64_t b, uint64_t c, uint64_t d,
                             uint64_t e, uint64_t f);
uint64_t NW_MS_ABI nw_abi_preserved(void);
#endif
