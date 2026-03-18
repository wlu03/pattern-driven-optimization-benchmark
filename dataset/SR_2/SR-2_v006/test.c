#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 500000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = N;
    float *X = malloc(500000 * sizeof(float));
    for (int k = 0; k < 500000; k++) X[k] = (float)(k % 100 - 50) * 0.1f;
    float *Y = malloc(500000 * sizeof(float));
    for (int k = 0; k < 500000; k++) Y[k] = (float)(k % 100 - 50) * 0.1f;
    float *Z = malloc(500000 * sizeof(float));
    for (int k = 0; k < 500000; k++) Z[k] = (float)(k % 100 - 50) * 0.1f;
    float alpha = (float)2.5f, beta = (float)1.5f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_slow = slow_sr2_v006(X, Y, Z, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_fast = fast_sr2_v006(X, Y, Z, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    /* compute expected inline — penalty inlined here, no dependency on slow/fast */
    float p = 0.0;
    for (int k = 1; k <= 26; k++) p += (float)sin(alpha * k) * (float)exp(-beta * k * 0.1);
    float expected = 0.0;
    for (int k = 0; k < N; k++) expected += alpha * X[k] * X[k] + beta * Y[k] + alpha * Z[k] + p;

    double rel = fabs((double)(r_slow - expected)) / fmax(fabs((double)expected), 1e-12);
    int correct = rel < 1e-2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X);
    free(Y);
    free(Z);
    return 0;
}