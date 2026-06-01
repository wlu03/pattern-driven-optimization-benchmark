typedef struct {
    int scale;
    unsigned char qs[16];     /* 32 quantized 4-bit values packed in 16 bytes */
    unsigned char pad[1024 - sizeof(int) - 16];  /* superblock padding (DS-4 stride) */
} block_q4k_v364;
int slow_comp_v364(block_q4k_v364 *blocks, int *block_indices, int n_groups, int n_reps) {
    int acc = 0;
    for (int r = 0; r < n_reps; r++) {
        /* indirect access via block_indices — defeats prefetcher */
        for (int g = 0; g < n_groups; g++) {
            int gi = block_indices[g];
            for (int b = 0; b < 8; b++) {
                block_q4k_v364 *blk = &blocks[gi * 8 + b];
                int s = blk->scale;
                /* touch multiple offsets in the padded struct to force several cache-line loads */
                volatile unsigned char t1 = blk->pad[128 - sizeof(int) - 16];
                volatile unsigned char t2 = blk->pad[256 - sizeof(int) - 16];
                volatile unsigned char t3 = blk->pad[384 - sizeof(int) - 16];
                volatile unsigned char t4 = blk->pad[512 - sizeof(int) - 16];
                volatile unsigned char t5 = blk->pad[640 - sizeof(int) - 16];
                volatile unsigned char t6 = blk->pad[768 - sizeof(int) - 16];
                volatile unsigned char t7 = blk->pad[896 - sizeof(int) - 16];
                volatile unsigned char t8 = blk->pad[1024 - sizeof(int) - 16 - 1];
                (void)t1; (void)t2; (void)t3; (void)t4; (void)t5; (void)t6; (void)t7; (void)t8;
                for (int k = 0; k < 16; k++) {
                    unsigned char p = blk->qs[k];
                    acc += (int)(p & 0x0F) * s;
                    acc += (int)((p >> 4) & 0x0F) * s;
                }
            }
        }
    }
    return acc;
}