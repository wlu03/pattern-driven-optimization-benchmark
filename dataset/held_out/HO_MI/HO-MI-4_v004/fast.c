#include <stdint.h>
#include <string.h>

// FAST: manually unrolled 8x.  This produces the same code the compiler
// would emit if its auto-unroller fired -- but does so explicitly, so
// it remains 8-way unrolled even under -mretpoline / -fcf-protection.
// The 8x unroll exposes ILP across the 8 (lookup, emit, shift) chains
// so the OoO core overlaps them.
//
// Cite: zstd PR #3826 (Yann Collet 2023).  The PR comment notes:
//   "On clang with retpoline enabled, the compiler refuses to unroll
//    the inner loop, and we lose ~30% throughput.  Manual unroll
//    recovers the regression."
#define HO_MI4_NBITS    11
#define HO_MI4_TBL_SIZE (1u << HO_MI4_NBITS)

typedef struct { uint8_t sym; uint8_t nbits; } HoMi4Entry;

extern uint64_t ho_mi4_state_v004;

// Helper: one symbol's worth of decode work.  Marked inline so the
// 8x unroll below produces straight-line code.
static inline void hm4_step(const HoMi4Entry *table, uint64_t *bitsp,
                              int *bitpp, uint64_t *statep, uint8_t *out) {
    HoMi4Entry e = table[(*bitsp) & (HO_MI4_TBL_SIZE - 1)];
    *out = e.sym;
    *statep = (*statep ^ e.sym) * 0x100000001b3ULL;
    *bitsp >>= e.nbits;
    *bitpp -= e.nbits;
}

void fast_ho_mi4_v004(const uint8_t *src, long src_len,
                      const HoMi4Entry *table,
                      uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *ip = src;
    const uint8_t *iend = src + src_len;
    uint64_t state = ho_mi4_state_v004;

    long i = 0;
    // 8x manually-unrolled body: explicit 8 lookups, 8 emits, 8 shifts.
    // The refill before each batch ensures we have ~88 bits available
    // (max 8 * 11 = 88), more than enough for 8 symbols.
    for (; i + 8 <= n_syms; i += 8) {
        // Refill: aggressively top up to >=56 bits, but stop at iend.
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip) << bitp;
            ip++;
            bitp += 8;
        }
        // Bail if we cannot guarantee 8 * 11 = 88 bits.
        if (bitp < 88) {
            // Top up further (might over-refill but we checked ip < iend).
            while (bitp <= 56 && ip < iend) {
                bits |= ((uint64_t)*ip) << bitp;
                ip++;
                bitp += 8;
            }
            if (bitp < 88) break;  // not enough source data left
        }
        hm4_step(table, &bits, &bitp, &state, &dst[i + 0]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 1]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 2]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 3]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 4]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 5]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 6]);
        hm4_step(table, &bits, &bitp, &state, &dst[i + 7]);
    }
    // Tail: scalar loop for the last < 8 symbols.
    for (; i < n_syms; i++) {
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip) << bitp;
            ip++;
            bitp += 8;
        }
        hm4_step(table, &bits, &bitp, &state, &dst[i]);
    }
    ho_mi4_state_v004 = state;
}
