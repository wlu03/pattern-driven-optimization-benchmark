#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define ROWS 500
#define COLS 1000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *A = malloc(ROWS * COLS * sizeof(float));
    for (int i = 0; i < ROWS * COLS; i++) A[i] = (float)(i % 100) * 0.01f + 0.0f;
    float *B = malloc(ROWS * COLS * sizeof(float));
    for (int i = 0; i < ROWS * COLS; i++) B[i] = (float)(i % 100) * 0.01f + 0.0f;
    float *C = malloc(ROWS * COLS * sizeof(float));
    for (int i = 0; i < ROWS * COLS; i++) C[i] = (float)(i % 100) * 0.01f + 0.0f;

    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_slow = slow_sr_1_v006(A, B, C, ROWS, COLS, 2.0f, 2.1f, 2.2f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_fast = fast_sr_1_v006(A, B, C, ROWS, COLS, 2.0f, 2.1f, 2.2f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    double err = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1e-12);
    double tol = 1e-2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, err < tol, ms_slow / fmax(ms_fast, 0.001));

    free(A);
    free(B);
    free(C);
    return 0;
}