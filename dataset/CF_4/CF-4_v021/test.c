#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 5000000

/* fn_ functions are defined in fast.c, shared via extern */
extern double fn_relu_v021(double x);
extern double fn_square_v021(double x);
extern double fn_scale_v021(double x);
extern double fn_negate_v021(double x);

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *in_arr = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) in_arr[i] = (double)(i % 200 - 100) * (double)0.1;
    double (*fn)(double) = fn_negate_v021;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) slow_cf4_v021(out_slow, in_arr, N, fn);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 5; r++) fast_cf4_v021(out_fast, in_arr, N, fn);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 5;

    int correct = 1;
    for (int i = 0; i < N; i++) {
        if (fabs((double)(out_slow[i]-out_fast[i])) > 1e-9) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}