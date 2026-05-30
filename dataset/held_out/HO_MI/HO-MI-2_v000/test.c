#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 64M doubles = 512 MB working set.  On NUMA this is well beyond any
// per-socket LLC so the slow path's remote-DRAM reads dominate.  On
// single-socket (Apple Silicon / GitHub CI) the parallel-init speedup
// comes from the init phase saturating multi-core write bandwidth that
// one thread cannot.  Either way the pattern teaches: parallel
// first-touch so the same threads that READ also INIT'd.
#define N (64L * 1024 * 1024)
#define N_THREADS 8

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    double *buf_slow = malloc(N * sizeof(double));
    double *buf_fast = malloc(N * sizeof(double));
    if (!buf_slow || !buf_fast) return 1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ho_mi2_v000(buf_slow, N, N_THREADS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ho_mi2_v000(buf_fast, N, N_THREADS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(buf_slow); free(buf_fast);
    return 0;
}
