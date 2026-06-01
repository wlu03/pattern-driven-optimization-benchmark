#include <stdint.h>
#include <string.h>

// FAST (defended): same conditional-move via mask, but the mask is
// computed through a volatile barrier that the compiler cannot see
// through.  The optimizer can no longer prove `mask` is a function of
// `(x == 0)`, so it cannot rewrite the loop into a memcpy/skip.  The
// hot loop becomes a true unconditional masked-OR over every byte.
//
// In a real BearSSL-style codebase this would use the `BR_CTZ_*` /
// CT macros' explicit `__asm__ volatile` barrier; the upcoming
// LLVM 22 `__builtin_ct_select` intrinsic will be the official
// portable replacement.
//
// Cite: Pornin IACR eprint 2025/435; BearSSL inner.h; LLVM RFC
// __builtin_ct_select.
void fast_ho_sr5_v003(uint8_t *dst, const uint8_t *src, int x, int len) {
    volatile uint64_t cond = (uint64_t)(((uint32_t)(x | -x)) >> 31) ^ 1;
    volatile uint64_t mask = -cond;
    for (int i = 0; i < len; i++) {
        // Re-read mask via volatile each iter so the compiler cannot
        // hoist the `is x zero?` test out and branch around the loop.
        uint64_t m = mask;
        dst[i] = (uint8_t)((dst[i] & m) | (src[i] & ~m));
    }
}
