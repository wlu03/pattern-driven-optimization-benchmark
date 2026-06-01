#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 3000000

#ifndef AOS_V010_DEFINED
#define AOS_V010_DEFINED
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
    double fx;
    double fy;
    double fz;
    double potential;
    double kinetic;
    double radius;
    double spin;
    double lifetime;
    double _pad[8];
} AoS_v010;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v010 *arr = malloc(N * sizeof(AoS_v010));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].x = (double)(i % 100) * 0.01 + 0.5;
        arr[i].y = (double)(i % 100) * 0.01 + 0.5;
        arr[i].z = (double)(i % 100) * 0.01 + 0.5;
        arr[i].vx = (double)(i % 100) * 0.01 + 0.5;
        arr[i].vy = (double)(i % 100) * 0.01 + 0.5;
        arr[i].vz = (double)(i % 100) * 0.01 + 0.5;
        arr[i].mass = (double)(i % 100) * 0.01 + 0.5;
        arr[i].charge = (double)(i % 100) * 0.01 + 0.5;
        arr[i].fx = (double)(i % 100) * 0.01 + 0.5;
        arr[i].fy = (double)(i % 100) * 0.01 + 0.5;
        arr[i].fz = (double)(i % 100) * 0.01 + 0.5;
        arr[i].potential = (double)(i % 100) * 0.01 + 0.5;
        arr[i].kinetic = (double)(i % 100) * 0.01 + 0.5;
        arr[i].radius = (double)(i % 100) * 0.01 + 0.5;
        arr[i].spin = (double)(i % 100) * 0.01 + 0.5;
        arr[i].lifetime = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 8; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_potential = malloc(N * sizeof(double));
    double *soa_kinetic = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_potential[i] = arr[i].potential;
    for (int i = 0; i < N; i++) soa_kinetic[i] = arr[i].kinetic;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v010(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v010(soa_potential, soa_kinetic, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_potential);
    free(soa_kinetic);
    return 0;
}