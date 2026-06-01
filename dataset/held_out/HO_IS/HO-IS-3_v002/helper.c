#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define HO_IS3_CHUNK_CAP 2048

typedef struct {
    int n_valid;
    int data[HO_IS3_CHUNK_CAP];
} HoIs3Chunk;

typedef struct {
    int *sel_vec;
    int  n_valid;
} HoIs3LogicalChunk;

// SLOW: per-chunk physical compaction -- allocate a dense buffer of
// size n_valid, memcpy the valid prefix in, sum-reduce, then free.
// This mirrors the "make a new contiguous buffer for every chunk"
// pattern that DuckDB's old code paid in head-tier scans.
__attribute__((noinline))
long long physical_compact_sum_ho_is3_v002(HoIs3Chunk *chunks, long n_chunks) {
    long long sum = 0;
    int *staging = malloc(HO_IS3_CHUNK_CAP * sizeof(int));
    if (!staging) return 0;
    for (long c = 0; c < n_chunks; c++) {
        int nv = chunks[c].n_valid;
        // Physical compaction: copy into a dense buffer (even for nv == 1).
        memcpy(staging, chunks[c].data, nv * sizeof(int));
        long long cs = 0;
        for (int i = 0; i < nv; i++) cs += staging[i];
        sum += cs;
    }
    free(staging);
    return sum;
}

// FAST: logical compaction -- iterate the selection-vector and read
// from the shared buffer.  No memcpy, no malloc, no contiguous-buffer
// setup.  When n_valid is 1 (the common CRF=2048 case) this is just
// one indirect read per chunk.
__attribute__((noinline))
long long logical_compact_sum_ho_is3_v002(int *shared_buffer,
                                            HoIs3LogicalChunk *chunks,
                                            long n_chunks) {
    long long sum = 0;
    for (long c = 0; c < n_chunks; c++) {
        int *sv = chunks[c].sel_vec;
        int nv = chunks[c].n_valid;
        long long cs = 0;
        for (int i = 0; i < nv; i++) cs += shared_buffer[sv[i]];
        sum += cs;
    }
    return sum;
}
