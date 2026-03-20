#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define M 3000
#define NN 3000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *a = malloc(M * sizeof(double));
    double *b = malloc(NN * sizeof(double));
    double *C_slow = calloc(M * NN, sizeof(double));
    double *C_fast = calloc(M * NN, sizeof(double));
    srand(42);
    for (int i = 0; i < M; i++) a[i] = (rand() % 1000 < 990) ? 0.0 : (double)(rand() % 10 + 1) * 0.1;
    for (int i = 0; i < NN; i++) b[i] = (rand() % 1000 < 990) ? 0.0 : (double)(rand() % 10 + 1) * 0.1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_v018(C_slow, a, b, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_v018(C_fast, a, b, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M * NN; i++) {
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(a); free(b); free(C_slow); free(C_fast);
    return 0;
}