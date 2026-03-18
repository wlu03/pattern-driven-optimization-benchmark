#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 20000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = (double *)malloc(N * sizeof(double));
    double *B = (double *)malloc(N * sizeof(double));
    for (int k = 0; k < N; k++) {
        A[k] = (double)((k % 100) + 1) * 0.1;
        B[k] = (double)((k % 97)  + 1) * 0.1;
    }
    double *out_s = (double *)malloc(N * sizeof(double));
    double *out_f = (double *)malloc(N * sizeof(double));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_hr1_v019(out_s, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_hr1_v019(out_f, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < N; i++) {
        double denom = fmax(fabs(out_s[i]), 1.0);
        if (fabs(out_s[i] - out_f[i]) / denom > 1e-9) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_s); free(out_f);
    return 0;
}