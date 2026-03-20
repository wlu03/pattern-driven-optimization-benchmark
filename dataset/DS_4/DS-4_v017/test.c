#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 1000000

#ifndef AOS_V017_DEFINED
#define AOS_V017_DEFINED
typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v017;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v017 *arr = malloc(N * sizeof(AoS_v017));
    for (int i = 0; i < N; i++) {
        arr[i].temp = (float)(i % 100) * 0.01 + 0.5;
        arr[i].humidity = (float)(i % 100) * 0.01 + 0.5;
        arr[i].pressure = (double)(i % 100) * 0.01 + 0.5;
        arr[i].wind_speed = (float)(i % 100) * 0.01 + 0.5;
        arr[i].wind_dir = (float)(i % 100) * 0.01 + 0.5;
        arr[i].light = (int)(i % 100) * 0.01 + 0.5;
        arr[i].noise = (int)(i % 100) * 0.01 + 0.5;
        arr[i].co2 = (float)(i % 100) * 0.01 + 0.5;
    }

    double *soa_light = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_light[i] = (double)arr[i].light;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_v017(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_v017(soa_light, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_light);
    return 0;
}