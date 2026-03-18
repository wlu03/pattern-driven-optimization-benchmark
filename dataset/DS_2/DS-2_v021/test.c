#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000
#define CHUNK 8
#define N_RESULTS ((N + CHUNK - 1) / CHUNK)

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *input = malloc(N * sizeof(double));
    double *res_slow = malloc(N_RESULTS * sizeof(double));
    double *res_fast = malloc(N_RESULTS * sizeof(double));
    for (int i = 0; i < N; i++) input[i] = (double)(i % 100 + 1) * (double)0.1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ds2_v021(res_slow, input, N, CHUNK);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ds2_v021(res_fast, input, N, CHUNK);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N_RESULTS; i++) {
        if (fabs((double)(res_slow[i]-res_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(input); free(res_slow); free(res_fast);
    return 0;
}