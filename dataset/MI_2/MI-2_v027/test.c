#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *A = malloc(N * sizeof(int));
    int *B = malloc(N * sizeof(int));
    int *out_slow = malloc(N * sizeof(int));
    int *out_fast = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) { A[i] = (int)(i%100+1); B[i] = (int)(i%50+1); }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) slow_mi2_v027(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) fast_mi2_v027(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    int correct = 1;
    for (int i = 0; i < N; i++) if (out_slow[i] != out_fast[i]) { correct = 0; break; }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}