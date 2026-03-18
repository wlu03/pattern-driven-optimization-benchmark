#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 20000000;
    float *A = malloc(20000000 * sizeof(float)); for (int k = 0; k < 20000000; k++) A[k] = (float)(k % 200) * 0.05f;
    float *B = malloc(20000000 * sizeof(float)); for (int k = 0; k < 20000000; k++) B[k] = (float)(k % 200) * 0.05f;
    float *out_s = malloc(n * sizeof(float));
    float *out_f = malloc(n * sizeof(float));
    struct timespec t0, t1;
    int n_reps = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf1_v009(out_s, A, B, n, 3);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf1_v009(out_f, A, B, n, 3);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (fabsf(out_s[i] - out_f[i]) > 1e-6f) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A);
    free(B);
    free(out_s); free(out_f);
    return 0;
}
