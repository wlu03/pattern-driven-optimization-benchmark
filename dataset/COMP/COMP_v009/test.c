#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int rows = 1000, cols = 1000;
    double *mat = malloc(rows * cols * sizeof(double));
    double *avgs_slow = malloc(cols * sizeof(double));
    double *avgs_fast = malloc(cols * sizeof(double));
    for (int k = 0; k < rows * cols; k++) mat[k] = (double)(k % 100) * 0.01;
    struct timespec t0, t1;
    int n_reps = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_v009(mat, avgs_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_v009(mat, avgs_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int j = 0; j < cols; j++) {
        if (fabs((double)(avgs_slow[j] - avgs_fast[j])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat); free(avgs_slow); free(avgs_fast);
    return 0;
}
