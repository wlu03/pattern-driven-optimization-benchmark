#include <stdint.h>

// FAST (defended): same per-bit decode, but the bit and mask are
// computed through a volatile barrier so the compiler cannot recognize
// the "(bit ? 1665 : 0)" pattern and rewrite it into a branch+cmov.
// The defended formulation forces the mask AND to be emitted
// unconditionally.  In a real ML-KEM implementation this would use
// the upcoming LLVM 22 __builtin_ct_select intrinsic; the volatile
// barrier is the portable defense until then.
//
// Cite: Schneider et al. arXiv:2410.13489 Example 3 + PQShield
// Clangover writeup + LLVM RFC __builtin_ct_select.
void fast_ho_sr6_v004(const uint8_t *msg, int16_t *r, int n_bytes) {
    for (int i = 0; i < n_bytes; i++) {
        // Pull the message byte through a volatile barrier so the
        // optimizer cannot see the bit extract as a branch decision.
        volatile uint8_t m = msg[i];
        for (int j = 0; j < 8; j++) {
            volatile int16_t bit = (int16_t)((m >> j) & 1);
            int16_t mask = -bit;
            // Re-read mask through a volatile temporary each iter so
            // the compiler cannot fold the "mask & 1665" into a select.
            volatile int16_t mv = mask;
            r[8 * i + j] = mv & 1665;
        }
    }
}
