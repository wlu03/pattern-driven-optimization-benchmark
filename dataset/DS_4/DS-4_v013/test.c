#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 2000000

#ifndef AOS_V013_DEFINED
#define AOS_V013_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v013;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v013 *arr = malloc(N * sizeof(AoS_v013));
    for (int i = 0; i < N; i++) {
        arr[i].px = (float)(i % 100) * 0.01 + 0.5;
        arr[i].py = (float)(i % 100) * 0.01 + 0.5;
        arr[i].pz = (float)(i % 100) * 0.01 + 0.5;
        arr[i].nx = (float)(i % 100) * 0.01 + 0.5;
        arr[i].ny = (float)(i % 100) * 0.01 + 0.5;
        arr[i].nz = (float)(i % 100) * 0.01 + 0.5;
        arr[i].u = (float)(i % 100) * 0.01 + 0.5;
        arr[i].v = (float)(i % 100) * 0.01 + 0.5;
    }

    double *soa_px = malloc(N * sizeof(double));
    double *soa_u = malloc(N * sizeof(double));
    double *soa_pz = malloc(N * sizeof(double));
    double *soa_nz = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_px[i] = (double)arr[i].px;
    for (int i = 0; i < N; i++) soa_u[i] = (double)arr[i].u;
    for (int i = 0; i < N; i++) soa_pz[i] = (double)arr[i].pz;
    for (int i = 0; i < N; i++) soa_nz[i] = (double)arr[i].nz;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_v013(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_v013(soa_px, soa_u, soa_pz, soa_nz, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_px);
    free(soa_u);
    free(soa_pz);
    free(soa_nz);
    return 0;
}