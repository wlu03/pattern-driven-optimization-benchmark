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

#define N_CHUNKS 8000
#define CHUNK_SIZE 2048

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(303);
    int *raw=(int*)malloc(N_CHUNKS*CHUNK_SIZE*sizeof(int));
    int *n_valid=(int*)malloc(N_CHUNKS*sizeof(int));
    int *valid_indices=(int*)malloc(N_CHUNKS*CHUNK_SIZE*sizeof(int));
    for(int i=0;i<N_CHUNKS*CHUNK_SIZE;i++) raw[i]=(int)((i%100)+1)*(int)0.01;
    /* ~39% of chunks have n_valid==1, rest random 2..chunk_size */
    for(int c=0;c<N_CHUNKS;c++){
        if (rand()%100<70) { n_valid[c]=1; valid_indices[c*CHUNK_SIZE]=rand()%CHUNK_SIZE; }
        else {
            /* non-1 chunks have a small handful of valid entries */
            int nv = 2 + rand()%8;
            n_valid[c]=nv;
            for(int k=0;k<nv;k++) valid_indices[c*CHUNK_SIZE+k]=k*7;
        }
    }
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_comp_v378(raw,n_valid,valid_indices,N_CHUNKS,CHUNK_SIZE); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_comp_v378(raw,n_valid,valid_indices,N_CHUNKS,CHUNK_SIZE); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(raw);free(n_valid);free(valid_indices);return correct?0:1;
}