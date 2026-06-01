#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 200k floats per pass x REPS = enough work to be timable, while each
// individual a[]/b[] (800 KB) fits in L2.  This keeps the loop
// FMA-throughput-bound where 4-lane SIMD wins.
#define N 140000
#define REPS 200

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    float *a_slow = malloc(N * sizeof(float));
    float *a_fast = malloc(N * sizeof(float));
    float *b      = malloc(N * sizeof(float));
    if (!a_slow || !a_fast || !b) return 1;

    for (long i = 0; i < N; i++) {
        a_slow[i] = (float)((i & 0xFFFF) * 0.001);
        a_fast[i] = a_slow[i];
        b[i]      = (float)(((i * 7 + 3) & 0xFFFF) * 0.0001);
    }

    float *a_init = malloc(N * sizeof(float));
    memcpy(a_init, a_slow, N * sizeof(float));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < REPS; r++) {
        memcpy(a_slow, a_init, N * sizeof(float));
        slow_ho_mi3_v004(a_slow, b, N);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < REPS; r++) {
        memcpy(a_fast, a_init, N * sizeof(float));
        fast_ho_mi3_v004(a_fast, b, N);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (long i = 0; i < N; i++) {
        if (fabsf(a_slow[i] - a_fast[i]) > 1e-4f) { correct = 0; break; }
    }
    free(a_init);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(a_slow); free(a_fast); free(b);
    return 0;
}
