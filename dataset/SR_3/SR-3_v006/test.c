#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 100000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *data = malloc(N * sizeof(float));
    float *res_slow = malloc(N * sizeof(float));
    float *res_fast = malloc(N * sizeof(float));
    srand(42);
    for (int i = 0; i < N; i++) data[i] = (float)(rand() % 1000) * 0.01f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr3_v006(data, res_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr3_v006(data, res_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        /* relative tolerance: large N float accumulation can diverge by > 1 ULP */
        double denom = fmax(fabs((double)res_slow[i]), 1.0);
        double err = fabs((double)(res_slow[i] - res_fast[i])) / denom;
        if (err > 1e-3) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(data); free(res_slow); free(res_fast);
    return 0;
}