typedef struct {
    int scales[8];        /* 8 scales contiguous */
    unsigned char qs[8*16];   /* 8 blocks of 16 packed bytes interleaved sequentially */
} block_q4k_x8_v601;
int fast_comp_v601(block_q4k_x8_v601 *xb, int n_groups, int n_reps) {
    int acc = 0;
    for (int r = 0; r < n_reps; r++) {
        /* sequential dense access — prefetcher fully utilized */
        for (int g = 0; g < n_groups; g++) {
            block_q4k_x8_v601 *blk = &xb[g];
            for (int b = 0; b < 8; b++) {
                int s = blk->scales[b];
                unsigned char *qsb = blk->qs + b * 16;
                for (int k = 0; k < 16; k++) {
                    unsigned char p = qsb[k];
                    acc += (int)(p & 0x0F) * s;
                    acc += (int)((p >> 4) & 0x0F) * s;
                }
            }
        }
    }
    return acc;
}