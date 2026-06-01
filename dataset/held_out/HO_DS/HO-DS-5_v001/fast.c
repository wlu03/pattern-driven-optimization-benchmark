#include <stdint.h>

#ifndef HO_DS5_BLOCK8_DEFINED
#define HO_DS5_BLOCK8_DEFINED
// Repacked layout: 8 blocks fused into one "Kx8" super-block.  All 8
// scales come first (32 bytes — fits in a single AVX2/NEON register),
// then 8*32 = 256 quant bytes in one contiguous stream.  This is the
// llama.cpp PR #12332 block_q4_Kx8 layout.
typedef struct {
    float   scales[8];
    uint8_t qs[8 * 32];
} HoDs5Block8;
#endif

double dequant_soa_ho_ds5_v001(HoDs5Block8 *super_blocks, long n_blocks);

double fast_ho_ds5_v001(HoDs5Block8 *super_blocks, long n_blocks) {
    return dequant_soa_ho_ds5_v001(super_blocks, n_blocks);
}
