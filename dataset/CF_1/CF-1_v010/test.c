#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 5000000;
    double *A = malloc(5000000 * sizeof(double)); for (int k = 0; k < 5000000; k++) A[k] = (double)(k % 200) * 0.05f;
    double *B = malloc(5000000 * sizeof(double)); for (int k = 0; k < 5000000; k++) B[k] = (double)(k % 200) * 0.05f;
    double *C = malloc(5000000 * sizeof(double)); for (int k = 0; k < 5000000; k++) C[k] = (double)(k % 200) * 0.05f;
    double *out_s = malloc(n * sizeof(double));
    double *out_f = malloc(n * sizeof(double));
    struct timespec t0, t1;
    int n_reps = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf1_v010(out_s, A, B, C, n, 1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf1_v010(out_f, A, B, C, n, 1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (fabs(out_s[i] - out_f[i]) > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A);
    free(B);
    free(C);
    free(out_s); free(out_f);
    return 0;
}
