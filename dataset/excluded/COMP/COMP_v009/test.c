#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
/* ── standardized correctness check (auto-injected) ─────────────────── */
static inline int _bench_close(double a, double b, double atol, double rtol) {
    double d = a - b; if (d < 0) d = -d;
    double mb = b; if (mb < 0) mb = -mb;
    return d <= atol + rtol * mb;
}
/* ── end ────────────────────────────────────────────────────────────── */

#define N_GROUPS 150000
#define N_REPS 1
typedef struct {
    double scale;
    unsigned char qs[16];
    unsigned char pad[1024 - sizeof(double) - 16];
} block_q4k_v009;
typedef struct {
    double scales[8];
    unsigned char qs[8*16];
} block_q4k_x8_v009;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(909);
    int n_blocks = N_GROUPS * 8;
    block_q4k_v009 *blocks=(block_q4k_v009*)malloc(n_blocks*sizeof(block_q4k_v009));
    block_q4k_x8_v009 *xb=(block_q4k_x8_v009*)malloc(N_GROUPS*sizeof(block_q4k_x8_v009));
    int *block_indices=(int*)malloc(N_GROUPS*sizeof(int));
    for(int i=0;i<n_blocks;i++){
        blocks[i].scale=(double)((i%100)+1)*(double)0.01;
        for(int k=0;k<16;k++) blocks[i].qs[k]=(unsigned char)((i*16+k)%256);
        /* init the pad offsets the slow path touches via volatile loads */
        blocks[i].pad[0] = (unsigned char)(i & 0xFF);
        blocks[i].pad[256 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>1) & 0xFF);
        blocks[i].pad[512 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>2) & 0xFF);
        blocks[i].pad[768 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>3) & 0xFF);
        blocks[i].pad[sizeof(blocks[i].pad)-1] = (unsigned char)(i & 0xFF);
    }
    /* shuffled index array — slow path uses indirect access to defeat prefetcher */
    for(int g=0;g<N_GROUPS;g++) block_indices[g]=g;
    for(int g=N_GROUPS-1;g>0;g--){int j=rand()%(g+1);int tmp=block_indices[g];block_indices[g]=block_indices[j];block_indices[j]=tmp;}
    for(int g=0;g<N_GROUPS;g++){
        int sg = block_indices[g];
        for(int b=0;b<8;b++){
            xb[g].scales[b]=blocks[sg*8+b].scale;
            memcpy(xb[g].qs+b*16, blocks[sg*8+b].qs, 16);
        }
    }
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rs=slow_comp_v009(blocks,block_indices,N_GROUPS,N_REPS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rf=fast_comp_v009(xb,N_GROUPS,N_REPS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(blocks);free(xb);free(block_indices);return correct?0:1;
}