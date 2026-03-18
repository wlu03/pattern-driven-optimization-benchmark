#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 1000000;
    double *x = malloc(n * sizeof(double));
    double *y_slow = malloc(n * sizeof(double));
    double *y_fast = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) { unsigned rng = (unsigned)i * 6364136223846793005u; x[i] = (rng % 100 < 50) ? 0.0 : (double)(rng % 100 + 1) * 0.01; }
    for (int i = 0; i < n; i++) y_slow[i] = (double)(i % 100) * 0.01;
    memcpy(y_fast, y_slow, n * sizeof(double));
    double alpha = (double)2.5;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_v028(y_slow, x, alpha, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_v028(y_fast, x, alpha, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-5) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(x); free(y_slow); free(y_fast);
    return 0;
}
