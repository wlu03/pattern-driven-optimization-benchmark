#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 500000
#define PERIOD 100

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = (double *)calloc(N, sizeof(double));
    double *B = (double *)malloc(N * sizeof(double));
    /* A is 99% sparse: only every PERIOD-th element is non-zero */
    for (int i = 0; i < N; i += PERIOD) A[i] = (double)(i % 97 + 1) * (double)0.1;
    for (int i = 0; i < N; i++) B[i] = (double)(i % 100 + 1) * (double)0.1;
    double *out_slow = (double *)calloc(N, sizeof(double));
    double *out_fast = (double *)calloc(N, sizeof(double));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) slow_is1_v008(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) fast_is1_v008(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}