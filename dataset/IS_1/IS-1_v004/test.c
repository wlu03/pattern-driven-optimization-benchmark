#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define M 300
#define K 300
#define NN 300

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *A = malloc(M * K * sizeof(float));
    float *B = malloc(K * NN * sizeof(float));
    float *C_slow = calloc(M * NN, sizeof(float));
    float *C_fast = calloc(M * NN, sizeof(float));
    srand(42);
    for (int i = 0; i < M * K; i++) A[i] = (rand() % 1000 < 950) ? 0.0f : (float)(rand() % 10 + 1) * 0.1f;
    for (int i = 0; i < K * NN; i++) B[i] = (rand() % 1000 < 950) ? 0.0f : (float)(rand() % 10 + 1) * 0.1f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_v004(C_slow, A, B, M, K, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_v004(C_fast, A, B, M, K, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M * NN; i++) {
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(C_slow); free(C_fast);
    return 0;
}