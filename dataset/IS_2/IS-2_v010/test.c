#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *in_arr = malloc(N * sizeof(float));
    float *out_slow = malloc(N * sizeof(float));
    float *out_fast = malloc(N * sizeof(float));
    /* 90% of values within threshold, 10% outliers */
    for (int i = 0; i < N; i++) {
        if (i % 100 < 90) in_arr[i] = (float)((i % 100) - 50) * (float)0.02f;
        else in_arr[i] = (float)(i % 50 + 10) * (float)1.0f;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is2_v010(out_slow, in_arr, N, (float)1.0f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is2_v010(out_fast, in_arr, N, (float)1.0f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-5) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}