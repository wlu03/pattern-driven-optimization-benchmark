#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 500000
#define W 128

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *arr = (double*)malloc((long)N * W * sizeof(double));
    for (long i = 0; i < (long)N * W; i++) arr[i] = (double)(i % 997 + 1) * 0.001;

    struct timespec t0, t1;
    volatile double sum_slow = 0, sum_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < N; i++) sum_slow += slow_ds3_v020(arr + (long)i * W);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < N; i++) sum_fast += fast_ds3_v020(arr + (long)i * W);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs(sum_slow - sum_fast) < 1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}