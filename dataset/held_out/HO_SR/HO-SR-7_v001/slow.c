#include <stdint.h>

#ifndef HO_SR7_ENTRY_DEFINED
#define HO_SR7_ENTRY_DEFINED
typedef struct { uint8_t sym; uint8_t nbits; } HoSr7Entry;
#endif

// SLOW: bit-extract loop where the shift amount comes from a runtime
// table entry (`entry.nbits`).  GCC cannot prove `entry.nbits < 64` --
// the C standard says shifting by >= the bit-width is UB -- so it
// inserts a runtime guard around the `<<` and `>>` ops.  On x86 the
// guard is typically a `cmp $63, %cl ; ja .Lub` pair which adds a
// pipeline bubble per iteration in the hot decode loop.
//
// Reference: zstd PR #3826 (Yann Collet 2023), comment block on
// "Shift-mask elides GCC's UB check".
#define HO_SR7_NBITS    11
#define HO_SR7_TBL_SIZE (1u << HO_SR7_NBITS)

void slow_ho_sr7_v001(const uint8_t *src, long src_len,
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
        // No mask on the shift amount; GCC must insert a UB guard
        // because `e.nbits` is loaded from memory and not range-proven.
        bits >>= e.nbits;
        bitp -= e.nbits;
    }
}
