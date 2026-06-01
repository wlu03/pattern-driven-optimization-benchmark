#include <stdlib.h>
#include <string.h>
#include <pthread.h>

// FAST: parallel first-touch.  Each worker thread writes the sentinel
// to its OWN page-range first, claiming those pages on the local NUMA
// node (Linux: first-touch policy).  When the same threads then sum
// those page ranges in parallel, all reads are local.  On a 2-socket
// box this recovers ~17% throughput (llama.cpp #12759 telemetry).  On
// a single-socket / Apple Silicon test machine the speedup is reduced
// because there's no remote-node DRAM, but the init phase still
// benefits from parallel zeroing bandwidth.
double parallel_sum_parallel_init_ho_mi2_v002(double *buf, long n, int n_threads);

double fast_ho_mi2_v002(double *buf, long n, int n_threads) {
    return parallel_sum_parallel_init_ho_mi2_v002(buf, n, n_threads);
}
