#include <stdint.h>
/* SLOW: hot loop with branchy if where compiler-chosen cmov-vs-branch
 * lowering is fragile under register pressure. Replicates rav1d's
 * documented fragility: a TxClass enum addition changed unrelated stack
 * usage and flipped LLVM from cmov to branch on this exact shape.
 * https://www.memorysafety.org/blog/rav1d-performance-optimization/ */
__attribute__((noinline))
static int32_t gen_tok_v003(int i, int seed) {
    /* Defeat constant-propagation: tokens are 50% nonzero, depending on i */
    return ((i * 2654435761u) ^ (unsigned)seed) & 1;
}

void slow_ho_cf3_v003(int32_t *rc_out, const int32_t *rc_in, int n, int seed) {
    int32_t rc = 0;
    int32_t a0=1,a1=2,a2=3,a3=4,a4=5,a5=6,a6=7,a7=8;
    int32_t b0=11,b1=12,b2=13,b3=14,b4=15,b5=16,b6=17,b7=18;
    for (int i = 0; i < n; i++) {
        int32_t tok = gen_tok_v003(i, seed);
        int32_t rc_i = rc_in[i];
        /* Branchy form: register pressure from a0..a7 + b0..b7 pushes
         * Clang/GCC toward emitting a branch instead of cmov here. */
        if (tok != 0) rc = rc_i;
        /* fake use of pressure locals so they don't get optimized out */
        a0 += rc; a1 += rc; a2 += rc; a3 += rc;
        a4 += rc; a5 += rc; a6 += rc; a7 += rc;
        b0 ^= rc; b1 ^= rc; b2 ^= rc; b3 ^= rc;
        b4 ^= rc; b5 ^= rc; b6 ^= rc; b7 ^= rc;
        rc_out[i] = rc + (a0^a1^a2^a3^a4^a5^a6^a7) + (b0^b1^b2^b3^b4^b5^b6^b7);
    }
}
