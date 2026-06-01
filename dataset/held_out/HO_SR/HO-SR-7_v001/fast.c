#include <stdint.h>

#ifndef HO_SR7_ENTRY_DEFINED
#define HO_SR7_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoSr7Entry;
#endif

// FAST: mask the shift amount with `& 0x3F` -- semantically equivalent
// to the slow version on x86 (the hardware shift instruction already
// uses the low 6 bits of the count), but tells GCC that the shift
// amount is provably < 64.  GCC eliminates the UB guard and emits a
// single shift instruction in the hot loop.
//
// Cite: zstd PR #3826 (Yann Collet 2023): "Mask shift amount to elide
// GCC's UB check on variable-amount shifts."  In zstd's Huffman fast
// loop this is part of the ~+5% throughput delta on GCC.
#define HO_SR7_NBITS    11
#define HO_SR7_TBL_SIZE (1u << HO_SR7_NBITS)

void fast_ho_sr7_v001(const uint8_t *src, long src_len,
                       const HoSr7Entry *table,
                       uint8_t *dst, long n_syms) {
    uint64_t bits = 0;
    int bitp = 0;
    const uint8_t *ip = src;
    const uint8_t *iend = src + src_len;
    for (long i = 0; i < n_syms; i++) {
        while (bitp <= 56 && ip < iend) {
            bits |= ((uint64_t)*ip) << bitp;
            ip++;
            bitp += 8;
        }
        HoSr7Entry e = table[bits & (HO_SR7_TBL_SIZE - 1)];
        dst[i] = e.sym;
        // Mask the shift amount to tell GCC it's in [0,63] -- elides the
        // UB guard.  Semantically a no-op since e.nbits is always < 12.
        bits >>= (e.nbits & 0x3F);
        bitp -= e.nbits;
    }
}
