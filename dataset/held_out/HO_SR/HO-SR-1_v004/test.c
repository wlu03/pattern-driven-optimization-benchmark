#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 140
#define REPS 50000   // 50k separate calls with the same key

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    int *arr = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) arr[i] = i % 100;

    struct timespec t0, t1;
    int key = 42;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long total_slow = 0;
    for (int r = 0; r < REPS; r++) total_slow += slow_ho_sr1_v004(arr, N, key);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long total_fast = 0;
    for (int r = 0; r < REPS; r++) total_fast += fast_ho_sr1_v004(arr, N, key);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (total_slow == total_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}
