#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 1000000

#ifndef AOS_V008_DEFINED
#define AOS_V008_DEFINED
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v008;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v008 *arr = malloc(N * sizeof(AoS_v008));
    for (int i = 0; i < N; i++) {
        arr[i].r = (int)(i % 100) * 0.01 + 0.5;
        arr[i].g = (int)(i % 100) * 0.01 + 0.5;
        arr[i].b = (int)(i % 100) * 0.01 + 0.5;
        arr[i].a = (int)(i % 100) * 0.01 + 0.5;
        arr[i].x = (int)(i % 100) * 0.01 + 0.5;
        arr[i].y = (int)(i % 100) * 0.01 + 0.5;
        arr[i].depth = (float)(i % 100) * 0.01 + 0.5;
        arr[i].normal_x = (float)(i % 100) * 0.01 + 0.5;
    }

    double *soa_g = malloc(N * sizeof(double));
    double *soa_b = malloc(N * sizeof(double));
    double *soa_y = malloc(N * sizeof(double));
    double *soa_normal_x = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_g[i] = (double)arr[i].g;
    for (int i = 0; i < N; i++) soa_b[i] = (double)arr[i].b;
    for (int i = 0; i < N; i++) soa_y[i] = (double)arr[i].y;
    for (int i = 0; i < N; i++) soa_normal_x[i] = (double)arr[i].normal_x;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_v008(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_v008(soa_g, soa_b, soa_y, soa_normal_x, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_g);
    free(soa_b);
    free(soa_y);
    free(soa_normal_x);
    return 0;
}