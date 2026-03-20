#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *x = malloc(N * sizeof(float));
    float *y_slow = malloc(N * sizeof(float));
    float *y_fast = malloc(N * sizeof(float));
    srand(42);
    for (int i = 0; i < N; i++) {
        x[i] = (rand() % 100 < 90) ? 0.0f : (float)(rand() % 10 + 1) * 0.1f;
        y_slow[i] = (float)(i % 50) * 0.01f;
    }
    memcpy(y_fast, y_slow, N * sizeof(float));
    float alpha = 2.5f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_v005(y_slow, x, alpha, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_v005(y_fast, x, alpha, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-6) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(x); free(y_slow); free(y_fast);
    return 0;
}