#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define ROWS 5000
#define COLS 2000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *mat = malloc(ROWS * COLS * sizeof(double));
    for (int k = 0; k < ROWS * COLS; k++) mat[k] = (double)(k % 100) * 0.01;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_mi4_v014(mat, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_mi4_v014(mat, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    int correct = (diff < 1e-2);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat);
    return 0;
}