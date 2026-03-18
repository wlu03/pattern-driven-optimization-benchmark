#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int m = 8, n = 8;
    int *grid = malloc(m * n * sizeof(int));
    for (int i = 0; i < m * n; i++) grid[i] = (i % 10) + 1;
    int r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = 100000;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_v021(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_v021(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(grid);
    return 0;
}
