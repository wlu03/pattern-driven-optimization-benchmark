#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 2000000
#define RANGE 100

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    int *arr_slow = malloc(N * sizeof(int));
    int *arr_fast = malloc(N * sizeof(int));
    srand(45);
    for (int i = 0; i < N; i++) arr_slow[i] = rand() % RANGE;
    memcpy(arr_fast, arr_slow, N * sizeof(int));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_is1_v003(arr_slow, N, RANGE);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_is1_v003(arr_fast, N, RANGE);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (arr_slow[i] != arr_fast[i]) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr_slow); free(arr_fast);
    return 0;
}
