#include <stdint.h>
#include <string.h>

// FAST: tighten the loop bound from `ilimit = src + SAFETY` to
// `ilowest = src`.  The fast loop's own invariant -- "each iteration
// consumes at most 7 bytes from src and 4 bytes to dst" -- guarantees
// safety as long as we stop refilling once ip reaches iend AND we
// bail out of the unrolled inner block when we cannot guarantee 44
// more bits in the accumulator.
//
// Net: the fast loop runs all the way to src_end and the slow-path
// tail handles only ~0 to a handful of trailing symbols, instead of
// ~SAFETY symbols.  Per zstd PR #3827, this is the textbook
// "tighten loop bound" pattern.
//
// Cite: zstd PR #3827 (Yann Collet 2023). Commit reports +28% / +30%.
#define HO_IS5_NBITS    11
#define HO_IS5_TBL_SIZE (1u << HO_IS5_NBITS)

typedef struct { uint8_t sym; uint8_t nbits; } HoIs5Entry;

extern long ho_is5_slow_path_tail_v003(const uint8_t **ipp, uint64_t *bitsp, int *bitpp,
                                        const uint8_t *iend, const HoIs5Entry *table,
                                        uint8_t *dst, long max_emit);

void fast_ho_is5_v003(const uint8_t *src, long src_len,
                       const HoIs5Entry *table,
                       uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *ip = src;
    const uint8_t *iend = src + src_len;
    uint8_t *op = dst;
    uint8_t *oend = dst + n_syms;

    while (op + 4 <= oend) {
        // Refill stops at iend (no SAFETY margin).
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip++) << bitp; bitp += 8;
        }
        // Bail when we can't guarantee 4 * 11 bits available.
        if (bitp < 44) break;
        HoIs5Entry e0 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e0.sym; bits >>= e0.nbits; bitp -= e0.nbits;
        HoIs5Entry e1 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e1.sym; bits >>= e1.nbits; bitp -= e1.nbits;
        HoIs5Entry e2 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e2.sym; bits >>= e2.nbits; bitp -= e2.nbits;
        HoIs5Entry e3 = table[bits & (HO_IS5_TBL_SIZE - 1)]; *op++ = e3.sym; bits >>= e3.nbits; bitp -= e3.nbits;
    }
    long remaining = oend - op;
    if (remaining > 0)
        ho_is5_slow_path_tail_v003(&ip, &bits, &bitp, iend, table, op, remaining);
}
