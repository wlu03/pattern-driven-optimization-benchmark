#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int m = 2000, n = 2000;
    float *A = malloc(m * n * sizeof(float));
    float *x = malloc(n * sizeof(float));
    float *y_slow = calloc(m, sizeof(float));
    float *y_fast = calloc(m, sizeof(float));
    for (int i = 0; i < m * n; i++) { unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < 80) ? 0.0f : (float)(rng % 100 + 1) * 0.01f; }
    for (int i = 0; i < n; i++) x[i] = (float)(i % 100 + 1) * 0.01f;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_v006(y_slow, A, x, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_v006(y_fast, A, x, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m; i++) {
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(x); free(y_slow); free(y_fast);
    return 0;
}
