#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int rows = 1000, cols = 1000;
    float *A = malloc(rows * cols * sizeof(float));
    float *B = malloc(rows * cols * sizeof(float));
    float *out_slow = malloc(rows * cols * sizeof(float));
    float *out_fast = malloc(rows * cols * sizeof(float));
    for (int k = 0; k < rows * cols; k++) { A[k] = (float)(k % 100 + 1) * 0.01f; B[k] = (float)(k % 97 + 1) * 0.01f; }
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_v002(out_slow, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_v002(out_fast, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {
        if (fabs((double)(out_slow[k] - out_fast[k])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}
