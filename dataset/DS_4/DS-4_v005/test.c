#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 2000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    AoS_v005 *arr = malloc(N * sizeof(AoS_v005));
    for (int i = 0; i < N; i++) {
        arr[i].id = (int)(i % 100) * 0.01 + 0.5;
        arr[i].timestamp = (double)(i % 100) * 0.01 + 0.5;
        arr[i].value = (double)(i % 100) * 0.01 + 0.5;
        arr[i].weight = (float)(i % 100) * 0.01 + 0.5;
        arr[i].category = (int)(i % 100) * 0.01 + 0.5;
        arr[i].flags = (int)(i % 100) * 0.01 + 0.5;
        arr[i].score = (double)(i % 100) * 0.01 + 0.5;
        arr[i].rank = (int)(i % 100) * 0.01 + 0.5;
    }

    double *soa_id = malloc(N * sizeof(double));
    double *soa_rank = malloc(N * sizeof(double));
    double *soa_value = malloc(N * sizeof(double));
    double *soa_category = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) soa_id[i] = (double)arr[i].id;
    for (int i = 0; i < N; i++) soa_rank[i] = (double)arr[i].rank;
    for (int i = 0; i < N; i++) soa_value[i] = (double)arr[i].value;
    for (int i = 0; i < N; i++) soa_category[i] = (double)arr[i].category;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_v005(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_v005(soa_id, soa_rank, soa_value, soa_category, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
    free(soa_id);
    free(soa_rank);
    free(soa_value);
    free(soa_category);
    return 0;
}