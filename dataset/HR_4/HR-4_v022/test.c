#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *arr = (double *)malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) arr[i] = (double)(i % 100 + 1) * 0.1;
    double scale = 1.5;

    struct timespec t0, t1;
    volatile double r_slow, r_fast;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_hr4_v022(arr, scale, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_hr4_v022(arr, scale, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;

    int correct = (fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0) < 1e-9) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}