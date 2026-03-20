#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 4000000

#ifndef AOS_V019_DEFINED
#define AOS_V019_DEFINED
typedef struct {
    double r;
    double g;
    double b;
    double a;
    double x;
    double y;
    double depth;
    double normal_x;
    double normal_y;
    double normal_z;
    double u;
    double v;
    double specular;
    double diffuse;
    double emissive;
    double opacity;
    double _pad[16];
} AoS_v019;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v019 *arr = malloc(N * sizeof(AoS_v019));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].r = (double)(i % 100) * 0.01 + 0.5;
        arr[i].g = (double)(i % 100) * 0.01 + 0.5;
        arr[i].b = (double)(i % 100) * 0.01 + 0.5;
        arr[i].a = (double)(i % 100) * 0.01 + 0.5;
        arr[i].x = (double)(i % 100) * 0.01 + 0.5;
        arr[i].y = (double)(i % 100) * 0.01 + 0.5;
        arr[i].depth = (double)(i % 100) * 0.01 + 0.5;
        arr[i].normal_x = (double)(i % 100) * 0.01 + 0.5;
        arr[i].normal_y = (double)(i % 100) * 0.01 + 0.5;
        arr[i].normal_z = (double)(i % 100) * 0.01 + 0.5;
        arr[i].u = (double)(i % 100) * 0.01 + 0.5;
        arr[i].v = (double)(i % 100) * 0.01 + 0.5;
        arr[i].specular = (double)(i % 100) * 0.01 + 0.5;
        arr[i].diffuse = (double)(i % 100) * 0.01 + 0.5;
        arr[i].emissive = (double)(i % 100) * 0.01 + 0.5;
        arr[i].opacity = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 16; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_y = malloc(N * sizeof(double));
    double *soa_g = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_y[i] = arr[i].y;
    for (int i = 0; i < N; i++) soa_g[i] = arr[i].g;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v019(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v019(soa_y, soa_g, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_y);
    free(soa_g);
    return 0;
}