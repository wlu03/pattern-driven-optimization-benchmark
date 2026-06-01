#include <stdint.h>

// FAST: logical compaction.  Instead of physically materializing a
// dense buffer per chunk, we keep a single 2048-element shared buffer
// and give each "chunk" a selection-vector of indices into it.  The
// hot sum loop reduces over the selection-vector indices -- no
// memcpy, no per-chunk allocation, no contiguous-buffer setup
// overhead.  When most chunks have n_valid == 1, the slow version
// pays ~2048 bytes of bookkeeping per chunk for a single element;
// the fast version pays 4 bytes (the one sel-vector entry).
//
// Reference: Qiao & Zhang, "Compacting Vectorized Execution"
// (SIGMOD'25) + DuckDB PR #14956 -- up to 3x on head-to-head bench.
typedef struct {
    int *sel_vec;     // indices into shared_buffer
    int  n_valid;
} HoIs3LogicalChunk;

long long logical_compact_sum_ho_is3_v001(int *shared_buffer,
                                            HoIs3LogicalChunk *chunks,
                                            long n_chunks);

long long fast_ho_is3_v001(int *shared_buffer,
                            HoIs3LogicalChunk *chunks,
                            long n_chunks) {
    return logical_compact_sum_ho_is3_v001(shared_buffer, chunks, n_chunks);
}
