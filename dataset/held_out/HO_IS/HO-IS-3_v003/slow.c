#include <stdint.h>
#include <string.h>

// SLOW: each chunk has its own 2048-element data buffer + a per-chunk
// n_valid count.  When ~39% of chunks contain just 1 valid element
// (the head end of a CRF=2048 vector tree), the slow code still
// memcpy()s those few elements into a dense compacted output -- one
// memcpy per chunk with hot setup overhead.  This is the "naive
// physical compaction" baseline in the DuckDB SIGMOD'25 paper.
//
// Reference: Qiao & Zhang, "Compacting Vectorized Execution"
// (SIGMOD'25) + DuckDB PR #14956.
#define HO_IS3_CHUNK_CAP 2048

typedef struct {
    int n_valid;
    int data[HO_IS3_CHUNK_CAP];
} HoIs3Chunk;

long long physical_compact_sum_ho_is3_v003(HoIs3Chunk *chunks, long n_chunks);

long long slow_ho_is3_v003(HoIs3Chunk *chunks, long n_chunks) {
    return physical_compact_sum_ho_is3_v003(chunks, n_chunks);
}
