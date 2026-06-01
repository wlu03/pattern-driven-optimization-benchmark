#include <stdint.h>
#include <string.h>
/* FAST: inline bitstream reads. No per-call function, no per-symbol EOB
 * check. Refill happens via unaligned 8-byte load when bitcount<32.
 * Pre-allocated padded input means no per-iteration bounds check. */

int32_t fast_ho_cf4_v004(const uint8_t *src, int n_bytes, int n_syms) {
    /* Caller's responsibility: src has >=8 trailing zero bytes of padding,
     * so refill never reads past the buffer. The test harness ensures this. */
    const uint8_t *cursor = src;
    uint64_t bitbuf = 0;
    int bitcount = 0;
    int32_t acc = 0;
    for (int i = 0; i < n_syms; i++) {
        if (bitcount < 5) {
            /* Branchless 8-byte refill — reads up to 8 bytes past cursor */
            uint64_t w;
            memcpy(&w, cursor, 8);
            bitbuf |= w << bitcount;
            int refill_bytes = (64 - bitcount) / 8;
            cursor   += refill_bytes;
            bitcount += refill_bytes * 8;
        }
        int v = (int)(bitbuf & 0x1f);
        bitbuf >>= 5;
        bitcount -= 5;
        acc += v;
    }
    return acc;
}
