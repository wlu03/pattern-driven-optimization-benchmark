#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 5000000;
    int *X = malloc(n * sizeof(int));
    int *Y = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) { X[i] = (int)(i % 100 + 1) * 0.01; Y[i] = (int)(i % 97 + 1) * 0.01; }
    int alpha = (int)2.5, beta = (int)1.7;
    int r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_v000(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_v000(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y);
    return 0;
}
