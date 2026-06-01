#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 1M ints; we run 3 distinct shapes -- fully ascending, partly sorted,
// and small-range random -- so the adaptive dispatch hits Tier 1
// (twice) and Tier 2 (once) where qsort always pays full O(n log n).
#define N 700000
#define RANGE 1000     // small enough that Tier 2 (counting sort) kicks in

// SLOW_CODE_HERE
// FAST_CODE_HERE

static int cmp_int(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

static void gen_ascending(int *out, long n) {
    for (long i = 0; i < n; i++) out[i] = (int)(i & 0xFFFF);
}
static void gen_random_small_range(int *out, long n, unsigned seed) {
    srand(seed);
    for (long i = 0; i < n; i++) out[i] = rand() % RANGE;
}

int main() {
    int *a_slow = malloc(N * sizeof(int));
    int *a_fast = malloc(N * sizeof(int));
    int *expected = malloc(N * sizeof(int));
    if (!a_slow || !a_fast || !expected) return 1;

    double total_slow_ms = 0, total_fast_ms = 0;
    int all_correct = 1;
    struct timespec t0, t1;

    // === Shape 1: fully ascending (Tier 1 should detect and return) ===
    gen_ascending(a_slow, N);
    memcpy(a_fast, a_slow, N * sizeof(int));
    memcpy(expected, a_slow, N * sizeof(int));
    qsort(expected, N, sizeof(int), cmp_int);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_is2_v004(a_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_slow_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_is2_v004(a_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_fast_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    for (long i = 0; i < N; i++) {
        if (a_slow[i] != expected[i] || a_fast[i] != expected[i]) {
            all_correct = 0; break;
        }
    }

    // === Shape 2: small-range random (Tier 2 should pick counting sort) ===
    gen_random_small_range(a_slow, N, 42);
    memcpy(a_fast, a_slow, N * sizeof(int));
    memcpy(expected, a_slow, N * sizeof(int));
    qsort(expected, N, sizeof(int), cmp_int);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_is2_v004(a_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_slow_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_is2_v004(a_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_fast_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    for (long i = 0; i < N; i++) {
        if (a_slow[i] != expected[i] || a_fast[i] != expected[i]) {
            all_correct = 0; break;
        }
    }

    // === Shape 3: partly sorted (first half ascending, second random) ===
    for (long i = 0; i < N; i++) a_slow[i] = (i < N/2) ? (int)i : rand();
    memcpy(a_fast, a_slow, N * sizeof(int));
    memcpy(expected, a_slow, N * sizeof(int));
    qsort(expected, N, sizeof(int), cmp_int);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_is2_v004(a_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_slow_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_is2_v004(a_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    total_fast_ms += (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    for (long i = 0; i < N; i++) {
        if (a_slow[i] != expected[i] || a_fast[i] != expected[i]) {
            all_correct = 0; break;
        }
    }

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           total_slow_ms, total_fast_ms, all_correct,
           total_slow_ms / fmax(total_fast_ms, 0.001));
    free(a_slow); free(a_fast); free(expected);
    return 0;
}
