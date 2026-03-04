#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) A[i] = (double)(i % 100) * 0.01;
    double *B = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) B[i] = (double)(i % 100) * 0.01;
    double *C = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) C[i] = (double)(i % 100) * 0.01;
    double *D = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) D[i] = (double)(i % 100) * 0.01;

    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_sr_1_v025(A, B, C, D, N, 2.0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_sr_1_v025(A, B, C, D, N, 2.0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    double err = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1e-12);
    double tol = 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, err < tol, ms_slow / fmax(ms_fast, 0.001));

    free(A);
    free(B);
    free(C);
    free(D);
    return 0;
}