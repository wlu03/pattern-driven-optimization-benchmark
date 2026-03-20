#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *X = malloc(N * sizeof(double));
    for (int k = 0; k < N; k++) X[k] = (double)(k % 100) * 0.01;
    double *Y = malloc(N * sizeof(double));
    for (int k = 0; k < N; k++) Y[k] = (double)(k % 100) * 0.01;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_sr2_v011(X, Y, N, 2.5, 1.7);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_sr2_v011(X, Y, N, 2.5, 1.7);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-4) || (diff < 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(X);
    free(Y);
    return 0;
}