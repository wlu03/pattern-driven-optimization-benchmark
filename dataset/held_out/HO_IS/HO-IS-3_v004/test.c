#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 1000 chunks; the DuckDB paper measured 39% of chunks at CRF=2048 have
// just n_valid == 1.  We pick a similar mix: 40% have n_valid==1, the
// rest have n_valid in [50, 200].  Slow pays the per-chunk memcpy
// setup even for the 1-element chunks; fast does a single indirect
// load.
#define N_CHUNKS 100000
#define HO_IS3_CHUNK_CAP 2048

typedef struct {
    int n_valid;
    int data[HO_IS3_CHUNK_CAP];
} HoIs3Chunk;

typedef struct {
    int *sel_vec;
    int  n_valid;
} HoIs3LogicalChunk;

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoIs3Chunk *chunks_slow = malloc(N_CHUNKS * sizeof(HoIs3Chunk));
    HoIs3LogicalChunk *chunks_fast = malloc(N_CHUNKS * sizeof(HoIs3LogicalChunk));
    int *shared = malloc(HO_IS3_CHUNK_CAP * sizeof(int));
    if (!chunks_slow || !chunks_fast || !shared) return 1;

    // Populate the shared buffer with values 0..2047 so any sum is
    // computable from selection indices.
    for (int i = 0; i < HO_IS3_CHUNK_CAP; i++) shared[i] = i + 1;

    srand(46);
    for (long c = 0; c < N_CHUNKS; c++) {
        int nv;
        if ((rand() & 0xF) < 6) {
            nv = 1;   // 6/16 ~= 37.5% are size-1 chunks
        } else {
            nv = 50 + (rand() % 151);  // [50, 200]
        }
        chunks_slow[c].n_valid = nv;
        chunks_fast[c].n_valid = nv;
        chunks_fast[c].sel_vec = malloc(nv * sizeof(int));
        for (int i = 0; i < nv; i++) {
            int idx = rand() % HO_IS3_CHUNK_CAP;
            chunks_slow[c].data[i] = shared[idx];
            chunks_fast[c].sel_vec[i] = idx;
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_slow = slow_ho_is3_v004(chunks_slow, N_CHUNKS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile long long r_fast = fast_ho_is3_v004(shared, chunks_fast, N_CHUNKS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = ((long long)r_slow == (long long)r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    for (long c = 0; c < N_CHUNKS; c++) free(chunks_fast[c].sel_vec);
    free(chunks_slow); free(chunks_fast); free(shared);
    return 0;
}
