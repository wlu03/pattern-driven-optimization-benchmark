#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = malloc(N * sizeof(double));
    double *B = malloc(N * sizeof(double));
    double *C = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) A[i] = (double)(i % 1000 + 1) * 0.001;
    for (int i = 0; i < N; i++) B[i] = (double)(i % 997  + 1) * 0.001;
    for (int i = 0; i < N; i++) C[i] = (double)(i % 991  + 1) * 0.001;
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));

    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) slow_is5_v019(out_slow, A, B, C, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6 / 5.0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) fast_is5_v019(out_fast, A, B, C, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6 / 5.0;

    double err = 0.0;
    for (int i = 0; i < N; i++) {
        double d = fabs((double)(out_slow[i] - out_fast[i])) / fmax(fabs((double)out_slow[i]), 1e-12);
        if (d > err) err = d;
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, err < 1e-10, ms_slow / fmax(ms_fast, 0.001));

    free(A); free(B); free(C);
    free(out_slow); free(out_fast);
    return 0;
}