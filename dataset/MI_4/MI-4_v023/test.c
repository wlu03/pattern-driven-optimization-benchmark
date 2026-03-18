#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int rows = 3000, cols = 1000;
    float *mat_slow = malloc(rows * cols * sizeof(float));
    float *mat_fast = malloc(rows * cols * sizeof(float));
    for (int k = 0; k < rows * cols; k++) mat_slow[k] = (float)((k % 100) + 1) * 0.01;
    memcpy(mat_fast, mat_slow, rows * cols * sizeof(float));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_mi4_v023(mat_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_mi4_v023(mat_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {
        if (fabs((double)(mat_slow[k] - mat_fast[k])) > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat_slow); free(mat_fast);
    return 0;
}
