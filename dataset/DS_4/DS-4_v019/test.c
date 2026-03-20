#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 2000000

#ifndef AOS_V019_DEFINED
#define AOS_V019_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
} AoS_v019;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v019 *arr = malloc(N * sizeof(AoS_v019));
    for (int i = 0; i < N; i++) {
        arr[i].time = (double)(i % 100) * 0.01 + 0.5;
        arr[i].x = (double)(i % 100) * 0.01 + 0.5;
        arr[i].y = (double)(i % 100) * 0.01 + 0.5;
        arr[i].energy = (float)(i % 100) * 0.01 + 0.5;
        arr[i].channel = (int)(i % 100) * 0.01 + 0.5;
        arr[i].quality = (int)(i % 100) * 0.01 + 0.5;
        arr[i].amplitude = (double)(i % 100) * 0.01 + 0.5;
    }

    double *soa_time = malloc(N * sizeof(double));
    double *soa_amplitude = malloc(N * sizeof(double));
    double *soa_y = malloc(N * sizeof(double));
    double *soa_energy = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_time[i] = (double)arr[i].time;
    for (int i = 0; i < N; i++) soa_amplitude[i] = (double)arr[i].amplitude;
    for (int i = 0; i < N; i++) soa_y[i] = (double)arr[i].y;
    for (int i = 0; i < N; i++) soa_energy[i] = (double)arr[i].energy;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_v019(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_v019(soa_time, soa_amplitude, soa_y, soa_energy, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_time);
    free(soa_amplitude);
    free(soa_y);
    free(soa_energy);
    return 0;
}