#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 1M unique 64-bit keys inserted; then 1000 cardinality polls (a
// dashboard / monitoring workload that calls cardinality() much more
// often than insert).  Slow is vanilla HLL (m=16384, 16 KB).  Fast is
// HyperLogLogLog (Karppa-Pagh KDD'22) with 4-bit-packed offsets +
// per-block 8-bit base (8.25 KB total), and 256-element bulking on the
// insert path.  The compressed register array fits in L1 once shared
// with other workload state, so the estimator pass is materially faster.
// Per-pattern correctness tolerance is 2% relative (HLL theoretical
// std-error at m=16384 is 0.81%, leaving headroom for HLLL saturation).
#define N        2000000
#define N_POLLS  1000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint64_t *keys = malloc(N * sizeof(uint64_t));
    if (!keys) return 1;
    uint64_t s = 0xdeadbeefcafebabeULL;
    for (long i = 0; i < N; i++) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        keys[i] = s | 1ULL;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long r_slow = slow_ho_al4_v003(keys, N, N_POLLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long r_fast = fast_ho_al4_v003(keys, N, N_POLLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Both estimators are HLL-quality; compare them with epsilon=2%.
    double rel_err = fabs((double)r_slow - (double)r_fast) /
                     fmax((double)r_slow, 1.0);
    int correct = (rel_err < 0.02);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys);
    return 0;
}
