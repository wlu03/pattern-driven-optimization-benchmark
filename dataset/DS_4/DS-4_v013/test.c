#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 2000000

#ifndef AOS_V013_DEFINED
#define AOS_V013_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    double z;
    double energy;
    double channel;
    double quality;
    double amplitude;
    double phase;
    double duration;
    double rate;
    double peak;
    double baseline;
    double snr;
    double trigger;
    double confidence;
    double _pad[16];
} AoS_v013;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v013 *arr = malloc(N * sizeof(AoS_v013));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].time = (double)(i % 100) * 0.01 + 0.5;
        arr[i].x = (double)(i % 100) * 0.01 + 0.5;
        arr[i].y = (double)(i % 100) * 0.01 + 0.5;
        arr[i].z = (double)(i % 100) * 0.01 + 0.5;
        arr[i].energy = (double)(i % 100) * 0.01 + 0.5;
        arr[i].channel = (double)(i % 100) * 0.01 + 0.5;
        arr[i].quality = (double)(i % 100) * 0.01 + 0.5;
        arr[i].amplitude = (double)(i % 100) * 0.01 + 0.5;
        arr[i].phase = (double)(i % 100) * 0.01 + 0.5;
        arr[i].duration = (double)(i % 100) * 0.01 + 0.5;
        arr[i].rate = (double)(i % 100) * 0.01 + 0.5;
        arr[i].peak = (double)(i % 100) * 0.01 + 0.5;
        arr[i].baseline = (double)(i % 100) * 0.01 + 0.5;
        arr[i].snr = (double)(i % 100) * 0.01 + 0.5;
        arr[i].trigger = (double)(i % 100) * 0.01 + 0.5;
        arr[i].confidence = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 16; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_baseline = malloc(N * sizeof(double));
    double *soa_trigger = malloc(N * sizeof(double));
    double *soa_peak = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_baseline[i] = arr[i].baseline;
    for (int i = 0; i < N; i++) soa_trigger[i] = arr[i].trigger;
    for (int i = 0; i < N; i++) soa_peak[i] = arr[i].peak;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v013(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v013(soa_baseline, soa_trigger, soa_peak, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_baseline);
    free(soa_trigger);
    free(soa_peak);
    return 0;
}