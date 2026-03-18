#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int m = 200, k = 200, n = 200;
    double *A = malloc(m * k * sizeof(double));
    double *B = malloc(k * n * sizeof(double));
    double *C_slow = calloc(m * n, sizeof(double));
    double *C_fast = calloc(m * n, sizeof(double));
    for (int i = 0; i < m * k; i++) { unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < 80) ? 0.0 : (double)(rng % 100 + 1) * 0.01; }
    for (int i = 0; i < k * n; i++) { unsigned rng = (unsigned)i * 2246822519u; B[i] = (rng % 100 < 80) ? 0.0 : (double)(rng % 100 + 1) * 0.01; }
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_v008(C_slow, A, B, m, k, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_v008(C_fast, A, B, m, k, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m * n; i++) {
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(C_slow); free(C_fast);
    return 0;
}
