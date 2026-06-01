#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 4k keys inserted, then 1M random lookups.  Insert phase is dominated
// by hashing+probing; lookup phase is dominated by hashing.  Both
// versions produce the same sum because both insert the same keys with
// the same values and answer the same queries -- the hash function
// only changes the bucket-index probe order, not the result.
#define N_KV 4096
#define NQ 1000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint64_t *keys = malloc(N_KV * sizeof(uint64_t));
    long long *vals = malloc(N_KV * sizeof(long long));
    uint64_t *queries = malloc(NQ * sizeof(uint64_t));
    if (!keys || !vals || !queries) return 1;

    // Generate 4096 unique 64-bit keys with deterministic distribution.
    srand(45);
    for (long i = 0; i < N_KV; i++) {
        keys[i] = ((uint64_t)rand() << 32) | (uint64_t)rand() | 1ull;  // never 0
        vals[i] = (long long)(i * 7 + 3);
    }
    // Queries are drawn uniformly from the inserted keys so every
    // lookup hits.
    for (long q = 0; q < NQ; q++) queries[q] = keys[rand() % N_KV];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_ho_sr2_v003(keys, vals, N_KV, queries, NQ);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_ho_sr2_v003(keys, vals, N_KV, queries, NQ);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys); free(vals); free(queries);
    return 0;
}
