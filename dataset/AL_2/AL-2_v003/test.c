#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_ITEMS 2000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *items = malloc(N_ITEMS * sizeof(double));
    double *arr_slow = malloc(N_ITEMS * sizeof(double));
    double *arr_fast = malloc(N_ITEMS * sizeof(double));
    unsigned rs = 42u;
    for (int i = 0; i < N_ITEMS; i++) {
        rs = rs * 1664525u + 1013904223u;
        items[i] = (double)(rs % 100000) * 0.01;
    }

    struct timespec t0, t1;
    int sz_s = 0, sz_f = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_al2_v003(arr_slow, &sz_s, items, N_ITEMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_al2_v003(arr_fast, &sz_f, items, N_ITEMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (sz_s == sz_f) ? 1 : 0;
    if (correct) for (int i = 0; i < sz_s; i++) if (fabs(arr_slow[i]-arr_fast[i]) > 1e-12) { correct=0; break; }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(items); free(arr_slow); free(arr_fast);
    return 0;
}