#include <stdint.h>

#ifndef HO_DS5_BLOCK_DEFINED
#define HO_DS5_BLOCK_DEFINED
// One quantized block: a 4-byte scale + 32 4-bit quants packed into
// 32 bytes (one byte per quant for simplicity).  This is the layout of
// e.g. llama.cpp's pre-PR-12332 block_q4_K type: a contiguous array of
// blocks where each block has its own scale.
typedef struct {
    float   scale;
    uint8_t qs[32];
} HoDs5Block;
#endif

double dequant_aos_ho_ds5_v004(HoDs5Block *blocks, long n_blocks);

double slow_ho_ds5_v004(HoDs5Block *blocks, long n_blocks) {
    return dequant_aos_ho_ds5_v004(blocks, n_blocks);
}
