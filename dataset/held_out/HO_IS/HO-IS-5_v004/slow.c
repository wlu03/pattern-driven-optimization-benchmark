#include <stdint.h>
#include <string.h>

// SLOW: Huffman "fast loop" with a conservative early-exit guard.  The
// loop invariant is that each iteration consumes at most 7 bytes from
// src.  The original zstd code kept a defensive 14-byte safety margin
// (ilimit = src + 14), forcing the fast loop to exit ~14 bytes early
// and hand the tail to the slow per-symbol path -- which is in a
// separate TU and carries the full bounds-checking defensive
// formulation (~5-7x cost per symbol vs the fast loop).
//
// We exaggerate the safety margin to 50 bytes here to amplify the
// effect into a measurable wall-clock signal under -O3; the original
// zstd PR #3827 (Yann Collet 2023) measured +28% / +30% with the
// canonical 14-byte margin in a full decode pipeline.
//
// Reference: zstd PR #3827.
#define HO_IS5_NBITS    11
#define HO_IS5_TBL_SIZE (1u << HO_IS5_NBITS)
#define HO_IS5_SAFETY   180

typedef struct { uint8_t sym; uint8_t nbits; } HoIs5Entry;

// Helper in a separate TU -- the compiler cannot inline + vectorize
// across the call boundary at -O3 -fno-lto.
extern long ho_is5_slow_path_tail_v004(const uint8_t **ipp, uint64_t *bitsp, int *bitpp,
                                        const uint8_t *iend, const HoIs5Entry *table,
                                        uint8_t *dst, long max_emit);

void slow_ho_is5_v004(const uint8_t *src, long src_len,
                       const HoIs5Entry *table,
                       uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *ip = src;
    const uint8_t *iend = src + src_len;
    // Conservative: stop fast loop SAFETY bytes before src_end.
    const uint8_t *ilimit = src + src_len - HO_IS5_SAFETY;
    uint8_t *op = dst;
    uint8_t *oend = dst + n_syms;

    // Fast loop: 4 symbols per iter, 7 bytes/iter refill.
    while (op + 4 <= oend && ip < ilimit) {
        while (bitp <= 56) { bits |= ((uint64_t)*ip++) << bitp; bitp += 8; }
        HoIs5Entry e0 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e0.sym; bits >>= e0.nbits; bitp -= e0.nbits;
        HoIs5Entry e1 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e1.sym; bits >>= e1.nbits; bitp -= e1.nbits;
        HoIs5Entry e2 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e2.sym; bits >>= e2.nbits; bitp -= e2.nbits;
        HoIs5Entry e3 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e3.sym; bits >>= e3.nbits; bitp -= e3.nbits;
    }
    long remaining = oend - op;
    if (remaining > 0)
        ho_is5_slow_path_tail_v004(&ip, &bits, &bitp, iend, table, op, remaining);
}
