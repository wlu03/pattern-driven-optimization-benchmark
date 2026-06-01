#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    float *src = malloc((size_t)N * sizeof(float));
    float *dst_slow = malloc((size_t)N * sizeof(float));
    float *dst_fast = malloc((size_t)N * sizeof(float));
    if (!src || !dst_slow || !dst_fast) return 1;
    for (int i = 0; i < N; i++) src[i] = (float)(i % 1000) * 0.001f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_hr1_v001(src, dst_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_hr1_v001(src, dst_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabsf(dst_slow[i] - dst_fast[i]) > 1e-5f) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(src); free(dst_slow); free(dst_fast);
    return 0;
}
