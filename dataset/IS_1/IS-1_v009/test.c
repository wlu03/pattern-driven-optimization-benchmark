#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define M 1000
#define NN 1000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = malloc(M * NN * sizeof(double));
    double *x = malloc(NN * sizeof(double));
    double *y_slow = calloc(M, sizeof(double));
    double *y_fast = calloc(M, sizeof(double));
    srand(42);
    for (int i = 0; i < M * NN; i++) A[i] = (rand() % 100 < 50) ? 0.0 : (double)(rand() % 10 + 1) * 0.1;
    for (int i = 0; i < NN; i++) x[i] = (double)(rand() % 10 + 1) * 0.1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_v009(y_slow, A, x, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_v009(y_fast, A, x, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M; i++) {
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(x); free(y_slow); free(y_fast);
    return 0;
}