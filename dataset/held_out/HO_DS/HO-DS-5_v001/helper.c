#include <stdint.h>
#include <string.h>

#ifndef HO_DS5_BLOCK_DEFINED
#define HO_DS5_BLOCK_DEFINED
typedef struct {
    float   scale;
    uint8_t qs[32];
} HoDs5Block;
#endif

#ifndef HO_DS5_BLOCK8_DEFINED
#define HO_DS5_BLOCK8_DEFINED
typedef struct {
    float   scales[8];
    uint8_t qs[8 * 32];
} HoDs5Block8;
#endif

// SLOW: read scale, then dequantize 32 quants per block.  The 36-byte
// stride means the vectorizer cannot fold consecutive blocks together,
// and the per-block sum must be accumulated independently.
__attribute__((noinline))
double dequant_aos_ho_ds5_v001(HoDs5Block *blocks, long n_blocks) {
    double sum = 0.0;
    for (long b = 0; b < n_blocks; b++) {
        float s = blocks[b].scale;
        uint8_t *qs = blocks[b].qs;
        float bs = 0.0f;
        for (int i = 0; i < 32; i++) {
            bs += (float)qs[i] * s;
        }
        sum += (double)bs;
    }
    return sum;
}

// FAST: Kx8 layout lets us reorganize the loop so the inner stride is
// over the 8 blocks at the same quant-index.  At quant-index i, we load
// 8 quants (one per block), 8 scales, multiply lane-wise, and add to an
// 8-lane vector accumulator.  After 32 iterations we horizontally
// reduce.  This is the exact loop body used in llama.cpp's
// ggml_vec_dot_q4_Kx8_q8_K kernel.
__attribute__((noinline))
double dequant_soa_ho_ds5_v001(HoDs5Block8 *super_blocks, long n_blocks) {
    long n_super = n_blocks / 8;
    double sum = 0.0;
    for (long s = 0; s < n_super; s++) {
        float acc[8] = {0,0,0,0,0,0,0,0};
        float sc[8];
        // Load scales[8] as a single 32-byte register (NEON Q reg / AVX ymm).
        memcpy(sc, super_blocks[s].scales, sizeof(sc));
        uint8_t *qs = super_blocks[s].qs;
        // Inner loop: 32 iterations, each touches 8 quants (one per
        // block at the same quant-index).  The compiler vectorizes the
        // 8-lane fma over `acc[]`.
        for (int i = 0; i < 32; i++) {
            uint8_t *row = qs + i * 8;  // [N.B. logical re-layout: see writer]
            for (int k = 0; k < 8; k++) {
                acc[k] += (float)row[k] * sc[k];
            }
        }
        float super = 0;
        for (int k = 0; k < 8; k++) super += acc[k];
        sum += (double)super;
    }
    return sum;
}
