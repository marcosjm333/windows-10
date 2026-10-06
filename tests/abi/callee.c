#include "internal/base.h"
uint64_t NW_MS_ABI nw_abi_callee(uint64_t a, uint64_t b, uint64_t c,
                                uint64_t d, uint64_t e, uint64_t f) {
    volatile uint64_t values[6] = {a, b, c, d, e, f};
    uint64_t result = 0;
    for (size_t i = 0; i < 6; ++i) result += values[i] * (i + 1);
    return result;
}
