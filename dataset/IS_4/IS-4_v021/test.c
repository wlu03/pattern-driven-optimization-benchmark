#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#define N 500000
#define N_SWAPS 2500

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *base = malloc(N * sizeof(int));
    int *arr_slow = malloc(N * sizeof(int));
    int *arr_fast = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) base[i] = i;
    /* Introduce ~0.5% local swaps */
    unsigned rs = 99u;
    for (int s = 0; s < N_SWAPS; s++) {
        rs = rs * 1664525u + 1013904223u;
        int i = (int)((rs >> 1) % (unsigned)(N - 1));
        int tmp = base[i]; base[i] = base[i+1]; base[i+1] = tmp;
    }
    memcpy(arr_slow, base, N * sizeof(int));
    memcpy(arr_fast, base, N * sizeof(int));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is4_v021(arr_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is4_v021(arr_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) if (arr_slow[i] != arr_fast[i]) { correct = 0; break; }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(base); free(arr_slow); free(arr_fast);
    return 0;
}