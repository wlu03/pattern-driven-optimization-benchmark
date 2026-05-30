#include <stdlib.h>
#include <string.h>
#include <pthread.h>

// SLOW: serial first-touch.  A single thread writes a sentinel byte to
// every page of the working set (which, on Linux first-touch
// allocators, claims every page on THIS thread's NUMA node).  Then the
// parallel sum below has to read from a single remote node for the
// worker threads — measured ~17% throughput loss in llama.cpp #12759.
// On macOS / single-socket the cost is mostly the serialized init
// itself (no parallel zeroing bandwidth).
//
// On a NUMA box the same code further loses on the read-back phase.
// Cite: ggerganov/llama.cpp#12759 (filed 2025-04-04).
double parallel_sum_serial_init_ho_mi2_v000(double *buf, long n, int n_threads);

double slow_ho_mi2_v000(double *buf, long n, int n_threads) {
    return parallel_sum_serial_init_ho_mi2_v000(buf, n, n_threads);
}
