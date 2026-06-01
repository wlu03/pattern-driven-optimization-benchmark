#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 2000000

#ifndef HO_DS1_RECORD_DEFINED
#define HO_DS1_RECORD_DEFINED
typedef struct {
    double hot_a;
    double hot_b;
    double cold[30];
} HoDs1Record;
#endif

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoDs1Record *recs = malloc(N * sizeof(HoDs1Record));
    double *hot_a = malloc(N * sizeof(double));
    double *hot_b = malloc(N * sizeof(double));
    if (!recs || !hot_a || !hot_b) return 1;

    for (int i = 0; i < N; i++) {
        double base = (double)(i % 100) * 0.01 + 0.5;
        recs[i].hot_a = base;
        recs[i].hot_b = base * 2.0;
        for (int j = 0; j < 30; j++) recs[i].cold[j] = base + j;
        hot_a[i] = recs[i].hot_a;
        hot_b[i] = recs[i].hot_b;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ho_ds1_v003(recs, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ho_ds1_v003(hot_a, hot_b, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(recs); free(hot_a); free(hot_b);
    return 0;
}
