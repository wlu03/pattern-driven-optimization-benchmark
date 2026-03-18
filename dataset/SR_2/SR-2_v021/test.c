#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 2000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = N;
    double *X = malloc(2000000 * sizeof(double));
    for (int k = 0; k < 2000000; k++) X[k] = (double)(k % 100 - 50) * 0.1;
    double *Y = malloc(2000000 * sizeof(double));
    for (int k = 0; k < 2000000; k++) Y[k] = (double)(k % 100 - 50) * 0.1;
    double alpha = (double)1.0, beta = (double)0.5;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_sr2_v021(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_sr2_v021(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    /* compute expected inline — penalty inlined here, no dependency on slow/fast */
    double p = 0.0;
    for (int k = 1; k <= 11; k++) p += (double)sin(alpha * k) * (double)exp(-beta * k * 0.1);
    double expected = 0.0;
    for (int k = 0; k < N; k++) expected += alpha * X[k] * X[k] + beta * Y[k] + p;

    double rel = fabs((double)(r_slow - expected)) / fmax(fabs((double)expected), 1e-12);
    int correct = rel < 1e-2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X);
    free(Y);
    return 0;
}