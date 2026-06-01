#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 1M unique 64-bit keys.  Slow does exact distinct-count via chained
// hash set; fast does HyperLogLog with m=16384 and harmonic-mean
// estimate.  HLL theoretical std-error is 0.81% at m=16384, so the
// correctness harness allows 2% relative error.
#define N 1500000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint64_t *keys = malloc(N * sizeof(uint64_t));
    if (!keys) return 1;
    // Deterministic distinct keys (LCG, never collides over 1M draws).
    uint64_t s = 0xdeadbeefcafebabeULL;
    for (long i = 0; i < N; i++) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        keys[i] = s | 1ULL;  // never zero
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long r_slow = slow_ho_al2_v002(keys, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long r_fast = fast_ho_al2_v002(keys, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Relative-error correctness check, epsilon = 0.02 (2%).  HLL
    // theoretical std-error at m=16384 is 1.04/sqrt(16384) ~ 0.81%.
    double rel_err = fabs((double)r_slow - (double)r_fast) /
                     fmax((double)r_slow, 1.0);
    int correct = (rel_err < 0.02);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys);
    return 0;
}
