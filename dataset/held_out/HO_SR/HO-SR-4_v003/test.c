#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// Small table, many calls -- the slow version's compiler-transformed
// direct-load wins on wall-clock because it short-circuits the loop;
// the fast version forces the full constant-time scan.  We do NOT
// reward speedup here -- the correctness metric is that both versions
// return the same value (the contents of table[secret_idx]).  This is
// an INVERTED-FRAMING pattern: the "slow" version IS faster in
// wall-clock, but it is the version that breaks CT security.  See
// metadata.json `novelty_rationale` for the full explanation.
#define N        2048
#define N_CALLS  100000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    int64_t *table = malloc(N * sizeof(int64_t));
    if (!table) return 1;
    uint64_t s = 0xdeadbeefULL;
    for (int i = 0; i < N; i++) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        table[i] = (int64_t)s;
    }

    int secret_idx = 777;
    int64_t r_slow = 0, r_fast = 0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) r_slow = slow_ho_sr4_v003(table, secret_idx, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long c = 0; c < N_CALLS; c++) r_fast = fast_ho_sr4_v003(table, secret_idx, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Correctness: both must return table[secret_idx].
    int correct = (r_slow == r_fast) && (r_slow == table[secret_idx]);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(table);
    return 0;
}
