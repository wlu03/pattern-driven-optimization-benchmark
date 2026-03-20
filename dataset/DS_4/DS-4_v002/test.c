#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 2000000

#ifndef AOS_V002_DEFINED
#define AOS_V002_DEFINED
typedef struct {
    double px;
    double py;
    double pz;
    double pw;
    double nx;
    double ny;
    double nz;
    double nw;
    double tu;
    double tv;
    double cr;
    double cg;
    double cb;
    double ca;
    double bone_w;
    double bone_id;
    double _pad[8];
} AoS_v002;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v002 *arr = malloc(N * sizeof(AoS_v002));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].px = (double)(i % 100) * 0.01 + 0.5;
        arr[i].py = (double)(i % 100) * 0.01 + 0.5;
        arr[i].pz = (double)(i % 100) * 0.01 + 0.5;
        arr[i].pw = (double)(i % 100) * 0.01 + 0.5;
        arr[i].nx = (double)(i % 100) * 0.01 + 0.5;
        arr[i].ny = (double)(i % 100) * 0.01 + 0.5;
        arr[i].nz = (double)(i % 100) * 0.01 + 0.5;
        arr[i].nw = (double)(i % 100) * 0.01 + 0.5;
        arr[i].tu = (double)(i % 100) * 0.01 + 0.5;
        arr[i].tv = (double)(i % 100) * 0.01 + 0.5;
        arr[i].cr = (double)(i % 100) * 0.01 + 0.5;
        arr[i].cg = (double)(i % 100) * 0.01 + 0.5;
        arr[i].cb = (double)(i % 100) * 0.01 + 0.5;
        arr[i].ca = (double)(i % 100) * 0.01 + 0.5;
        arr[i].bone_w = (double)(i % 100) * 0.01 + 0.5;
        arr[i].bone_id = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 8; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_cb = malloc(N * sizeof(double));
    double *soa_cg = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_cb[i] = arr[i].cb;
    for (int i = 0; i < N; i++) soa_cg[i] = arr[i].cg;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v002(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v002(soa_cb, soa_cg, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_cb);
    free(soa_cg);
    return 0;
}