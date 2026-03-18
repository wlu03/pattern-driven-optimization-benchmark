#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 1000000;
    float *A = malloc(n * sizeof(float));
    float *B = malloc(n * sizeof(float));
    for (int i = 0; i < n; i++) { unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < 95) ? 0.0f : (float)(rng % 100 + 1) * 0.01f; }
    for (int i = 0; i < n; i++) { unsigned rng = (unsigned)(i + n) * 2246822519u; B[i] = (rng % 100 < 95) ? 0.0f : (float)(rng % 100 + 1) * 0.01f; }
    float r_slow = 0.0f, r_fast = 0.0f;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_is1_v018(A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_is1_v018(A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs((double)(r_slow - r_fast)) < 1e-4 * fmax(fabs((double)r_slow), 1.0);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}
