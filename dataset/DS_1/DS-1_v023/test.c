#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_KEYS 1000
#define N_QUERIES 500
#define HT_SIZE 32768

extern void ds1_build_v023(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n);

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *keys   = malloc(N_KEYS * sizeof(int));
    int *values = malloc(N_KEYS * sizeof(int));
    int *queries = malloc(N_QUERIES * sizeof(int));
    for (int i = 0; i < N_KEYS; i++) { keys[i] = i * 7 + 13; values[i] = i * 3; }
    unsigned rs = 42u;
    for (int i = 0; i < N_QUERIES; i++) {
        rs = rs * 1664525u + 1013904223u;
        queries[i] = keys[(rs >> 1) % N_KEYS];
    }

    int *hk = calloc(HT_SIZE, sizeof(int));
    int *hv = calloc(HT_SIZE, sizeof(int));
    int *ho = calloc(HT_SIZE, sizeof(int));
    ds1_build_v023(hk, hv, ho, HT_SIZE, keys, values, N_KEYS);

    struct timespec t0, t1;
    volatile int sum_slow = 0, sum_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 20; r++)
        for (int i = 0; i < N_QUERIES; i++) sum_slow += slow_ds1_v023(keys, values, N_KEYS, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 20;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 20; r++)
        for (int i = 0; i < N_QUERIES; i++) sum_fast += fast_ds1_v023(hk, hv, ho, HT_SIZE, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 20;

    int correct = (sum_slow == sum_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys); free(values); free(queries); free(hk); free(hv); free(ho);
    return 0;
}