#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int m = 1000, n = 1000;
    float *a = malloc(m * sizeof(float));
    float *b = malloc(n * sizeof(float));
    float *C_slow = calloc(m * n, sizeof(float));
    float *C_fast = calloc(m * n, sizeof(float));
    for (int i = 0; i < m; i++) { unsigned rng = (unsigned)i * 6364136223846793005u; a[i] = (rng % 100 < 80) ? 0.0f : (float)(rng % 100 + 1) * 0.01f; }
    for (int i = 0; i < n; i++) { unsigned rng = (unsigned)(i + m) * 2246822519u; b[i] = (rng % 100 < 80) ? 0.0f : (float)(rng % 100 + 1) * 0.01f; }
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_v020(C_slow, a, b, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_v020(C_fast, a, b, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m * n; i++) {
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(a); free(b); free(C_slow); free(C_fast);
    return 0;
}
