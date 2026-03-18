#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *arr_slow = malloc(N * sizeof(double));
    double *arr_fast = malloc(N * sizeof(double));
    double *expected = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) arr_slow[i] = arr_fast[i] = expected[i] = (double)(i % 100 + 1) * 0.01;

    double base = (double)2.0;

    /* compute expected inline — independent of slow/fast implementations */
    double scale = 0.0;
    for (int k = 1; k <= 42; k++) scale += (double)sin(base * k * 2.0);
    for (int i = 0; i < N; i++) expected[i] *= scale;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr1_v010(arr_slow, N, base);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr1_v010(arr_fast, N, base);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        double diff = fabs((double)(arr_slow[i] - expected[i])) / fmax(fabs((double)expected[i]), 1e-12);
        if (diff > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr_slow); free(arr_fast); free(expected);
    return 0;
}