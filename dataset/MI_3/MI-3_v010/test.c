#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 500000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *data = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) data[i] = (double)(i % 100 + 1) * (double)0.1;

    struct timespec t0, t1;
    volatile double r_slow, r_fast;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_slow = slow_mi3_v010(data, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_fast = fast_mi3_v010(data, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1e-12) < 1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(data);
    return 0;
}