#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000
#define N_REPS 20

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *arr = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) arr[i] = (double)(i % 100) * (double)0.05;
    arr[N / 2] = (double)11.0;  /* Violation at middle position */

    struct timespec t0, t1;
    volatile int r_slow = 0, r_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < N_REPS; r++) r_slow = slow_is3_v002(arr, N, (double)10.0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / N_REPS;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < N_REPS; r++) r_fast = fast_is3_v002(arr, N, (double)10.0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / N_REPS;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}