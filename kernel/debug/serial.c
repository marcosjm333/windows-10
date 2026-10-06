#include "arch/x64.h"
#include "internal/debug.h"

static uint32_t writer;
static uint64_t sequence, dropped;
static bool available;
static const char *const categories[] = {
    "BOOT", "HAL", "CPU", "MM", "PFN", "VM", "SCHED", "PS", "OB", "IO",
    "PNP", "POWER", "SEC", "REG", "LDR", "PE", "DPC", "APC", "IRQ", "LOCK",
    "DRIVER", "BUGCHECK"
};
static const char *const levels[] = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"};
static bool put(char c) {
    if (!available) return false;
    for (unsigned i = 0; i < 100000; ++i) {
        if ((nw_in8(0x3fd) & 0x20) != 0) { nw_out8(0x3f8, (uint8_t)c); return true; }
        nw_pause();
    }
    available = false;
    return false;
}
static void text(const char *s) { while (*s) { if (!put(*s++)) break; } }
static void hex(uint64_t n) {
    const char digits[] = "0123456789abcdef";
    text("0x");
    for (unsigned i = 16; i != 0; --i) (void)put(digits[(n >> ((i - 1) * 4)) & 15]);
}
void nw_serial_init(void) {
    nw_out8(0x3f9, 0);
    nw_out8(0x3fb, 0x80);
    nw_out8(0x3f8, 1);
    nw_out8(0x3f9, 0);
    nw_out8(0x3fb, 3);
    nw_out8(0x3fa, 0xc7);
    nw_out8(0x3fc, 3);
    available = nw_in8(0x3fd) != 0xff;
}
void nw_log(NwCategory category, NwLevel level, const char *event, uint64_t a, uint64_t b) {
    if (__atomic_exchange_n(&writer, 1, __ATOMIC_ACQUIRE) != 0) {
        (void)__atomic_fetch_add(&dropped, 1, __ATOMIC_RELAXED);
        return; /* NMI/reentry must not wait for an interrupted writer. */
    }
    text("seq="); hex(sequence++);
    text(" cpu=boot thread=NA irql=NA time=NA category=");
    text((unsigned)category < sizeof(categories) / sizeof(categories[0]) ? categories[category] : "UNKNOWN");
    text(" level="); text((unsigned)level < 6 ? levels[level] : "UNKNOWN");
    text(" event="); text(event);
    text(" a="); hex(a); text(" b="); hex(b);
    text(" dropped="); hex(__atomic_load_n(&dropped, __ATOMIC_RELAXED));
    text("\r\n");
    __atomic_store_n(&writer, 0, __ATOMIC_RELEASE);
}
