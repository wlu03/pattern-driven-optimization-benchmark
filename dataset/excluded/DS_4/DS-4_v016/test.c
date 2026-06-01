#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 4000000

#ifndef AOS_V016_DEFINED
#define AOS_V016_DEFINED
typedef struct {
    double id;
    double timestamp;
    double value;
    double weight;
    double category;
    double flags;
    double score;
    double rank;
    double lat;
    double lon;
    double elevation;
    double accuracy;
    double speed;
    double heading;
    double age;
    double priority;
    double _pad[8];
} AoS_v016;
#endif

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v016 *arr = malloc(N * sizeof(AoS_v016));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return 1; }
    for (int i = 0; i < N; i++) {
        arr[i].id = (double)(i % 100) * 0.01 + 0.5;
        arr[i].timestamp = (double)(i % 100) * 0.01 + 0.5;
        arr[i].value = (double)(i % 100) * 0.01 + 0.5;
        arr[i].weight = (double)(i % 100) * 0.01 + 0.5;
        arr[i].category = (double)(i % 100) * 0.01 + 0.5;
        arr[i].flags = (double)(i % 100) * 0.01 + 0.5;
        arr[i].score = (double)(i % 100) * 0.01 + 0.5;
        arr[i].rank = (double)(i % 100) * 0.01 + 0.5;
        arr[i].lat = (double)(i % 100) * 0.01 + 0.5;
        arr[i].lon = (double)(i % 100) * 0.01 + 0.5;
        arr[i].elevation = (double)(i % 100) * 0.01 + 0.5;
        arr[i].accuracy = (double)(i % 100) * 0.01 + 0.5;
        arr[i].speed = (double)(i % 100) * 0.01 + 0.5;
        arr[i].heading = (double)(i % 100) * 0.01 + 0.5;
        arr[i].age = (double)(i % 100) * 0.01 + 0.5;
        arr[i].priority = (double)(i % 100) * 0.01 + 0.5;
        for (int p = 0; p < 8; p++) arr[i]._pad[p] = 0.0;
    }

    double *soa_age = malloc(N * sizeof(double));
    double *soa_rank = malloc(N * sizeof(double));
    double *soa_timestamp = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_age[i] = arr[i].age;
    for (int i = 0; i < N; i++) soa_rank[i] = arr[i].rank;
    for (int i = 0; i < N; i++) soa_timestamp[i] = arr[i].timestamp;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_slow = slow_ds4_v016(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    volatile double r_fast = fast_ds4_v016(soa_age, soa_rank, soa_timestamp, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)r_slow - (double)r_fast);
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_age);
    free(soa_rank);
    free(soa_timestamp);
    return 0;
}