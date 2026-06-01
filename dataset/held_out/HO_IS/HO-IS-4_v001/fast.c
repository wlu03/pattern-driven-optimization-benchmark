#include <stdint.h>
#include <string.h>

// FAST: 4-stream interleaved Huffman decoder.  The input is split into
// 4 independent bitstreams; we maintain 4 separate (bits, bitp, sp,
// dst) state vectors and step them in lock-step at the micro-op
// level.  Each stream's iteration is still a serial chain of length
// ~5-7 cycles, but the four streams' chains are mutually independent,
// so the OoO core overlaps them and the per-symbol throughput goes
// from ~5-7 cycles to ~1.5-2 cycles.  This is exactly the trick zstd
// uses in its Huffman decoder (Collet, 4-stream "X4" mode).
//
// Output is partitioned into 4 segments; each stream emits into its
// own dst region with an independent write pointer so there is no
// false-sharing on the store side either.
//
// Cite: Yann Collet, zstd FSE/Huffman 4-stream decoder (2015); Fabian
// Giesen, "Reading bits in far too many ways" parts 1-3 (2023).
#define HO_IS4_NBITS    11
#define HO_IS4_TBL_SIZE (1u << HO_IS4_NBITS)

typedef struct { uint8_t sym; uint8_t nbits; } HoIs4Entry;

void fast_ho_is4_v001(const uint8_t *src0, long len0,
                      const uint8_t *src1, long len1,
                      const uint8_t *src2, long len2,
                      const uint8_t *src3, long len3,
                      const HoIs4Entry *table,
                      uint8_t *dst, long n_per_stream) {
    uint64_t b0 = 0, b1 = 0, b2 = 0, b3 = 0;
    int p0 = 0, p1 = 0, p2 = 0, p3 = 0;
    const uint8_t *sp0 = src0, *se0 = src0 + len0;
    const uint8_t *sp1 = src1, *se1 = src1 + len1;
    const uint8_t *sp2 = src2, *se2 = src2 + len2;
    const uint8_t *sp3 = src3, *se3 = src3 + len3;
    uint8_t *d0 = dst + 0 * n_per_stream;
    uint8_t *d1 = dst + 1 * n_per_stream;
    uint8_t *d2 = dst + 2 * n_per_stream;
    uint8_t *d3 = dst + 3 * n_per_stream;

    for (long i = 0; i < n_per_stream; i++) {
        // Refill all 4 streams up front -- order-insensitive.
        while (p0 <= 56 && sp0 < se0) { b0 |= ((uint64_t)(*sp0++)) << p0; p0 += 8; }
        while (p1 <= 56 && sp1 < se1) { b1 |= ((uint64_t)(*sp1++)) << p1; p1 += 8; }
        while (p2 <= 56 && sp2 < se2) { b2 |= ((uint64_t)(*sp2++)) << p2; p2 += 8; }
        while (p3 <= 56 && sp3 < se3) { b3 |= ((uint64_t)(*sp3++)) << p3; p3 += 8; }

        // 4 independent (lookup, emit, shift) chains -- ILP city.
        HoIs4Entry e0 = table[b0 & (HO_IS4_TBL_SIZE - 1)];
        HoIs4Entry e1 = table[b1 & (HO_IS4_TBL_SIZE - 1)];
        HoIs4Entry e2 = table[b2 & (HO_IS4_TBL_SIZE - 1)];
        HoIs4Entry e3 = table[b3 & (HO_IS4_TBL_SIZE - 1)];
        d0[i] = e0.sym;
        d1[i] = e1.sym;
        d2[i] = e2.sym;
        d3[i] = e3.sym;
        b0 >>= e0.nbits; p0 -= e0.nbits;
        b1 >>= e1.nbits; p1 -= e1.nbits;
        b2 >>= e2.nbits; p2 -= e2.nbits;
        b3 >>= e3.nbits; p3 -= e3.nbits;
    }
}
