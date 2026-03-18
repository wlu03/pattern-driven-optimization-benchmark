#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *in_arr  = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));
    /* 95% of values within threshold, 5% outliers */
    for (int i = 0; i < N; i++) {
        if (i % 100 < 95)
            in_arr[i] = (double)((i % 100) - 50) * (double)0.01;
        else
            in_arr[i] = (double)(i % 50 + 10) * (double)0.5;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++) slow_is2_v017(out_slow, in_arr, N, (double)0.5);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++) fast_is2_v017(out_fast, in_arr, N, (double)0.5);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-9) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}