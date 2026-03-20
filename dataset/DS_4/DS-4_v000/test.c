#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 3000000

#ifndef AOS_V000_DEFINED
#define AOS_V000_DEFINED
typedef struct {
    double temp;
    double humidity;
    double pressure;
    double wind_speed;
    double wind_dir;
    double light;
    double noise;
    double co2;
    double pm25;
    double pm10;
    double ozone;
    double radiation;
    double voltage;
    double current;
    double frequency;
    double signal;
    double _pad[16];
} AoS_v000;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v000 *arr = malloc(N * sizeof(AoS_v000));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].temp = (double)(i % 100) * 0.01 + 0.5;
        arr[i].humidity = (double)(i % 100) * 0.01 + 0.5;
        arr[i].pressure = (double)(i % 100) * 0.01 + 0.5;
        arr[i].wind_speed = (double)(i % 100) * 0.01 + 0.5;
        arr[i].wind_dir = (double)(i % 100) * 0.01 + 0.5;
        arr[i].light = (double)(i % 100) * 0.01 + 0.5;
        arr[i].noise = (double)(i % 100) * 0.01 + 0.5;
        arr[i].co2 = (double)(i % 100) * 0.01 + 0.5;
        arr[i].pm25 = (double)(i % 100) * 0.01 + 0.5;
        arr[i].pm10 = (double)(i % 100) * 0.01 + 0.5;
        arr[i].ozone = (double)(i % 100) * 0.01 + 0.5;
        arr[i].radiation = (double)(i % 100) * 0.01 + 0.5;
        arr[i].voltage = (double)(i % 100) * 0.01 + 0.5;
        arr[i].current = (double)(i % 100) * 0.01 + 0.5;
        arr[i].frequency = (double)(i % 100) * 0.01 + 0.5;
        arr[i].signal = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 16; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_pressure = malloc(N * sizeof(double));
    double *soa_ozone = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_pressure[i] = arr[i].pressure;
    for (int i = 0; i < N; i++) soa_ozone[i] = arr[i].ozone;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v000(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v000(soa_pressure, soa_ozone, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_pressure);
    free(soa_ozone);
    return 0;
}