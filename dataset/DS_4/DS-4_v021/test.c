#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v021;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 5000000;
    AoS_v021 *arr = malloc(n * sizeof(AoS_v021));
    double *soa_rank = malloc(5000000 * sizeof(double));
    double *soa_category = malloc(5000000 * sizeof(double));
    double *soa_weight = malloc(5000000 * sizeof(double));
    double *soa_id = malloc(5000000 * sizeof(double));
    for (int i = 0; i < 5000000; i++) {
        int iv = (i % 997) + 1;
        double dv = (double)iv * 0.001;
        arr[i].rank = iv * 1;
        arr[i].category = iv * 2;
        arr[i].weight = dv * 3;
        arr[i].id = iv * 4;
        soa_rank[i] = (double)(iv * 1);
        soa_category[i] = (double)(iv * 2);
        soa_weight[i] = (double)(dv * 3);
        soa_id[i] = (double)(iv * 4);
    }
    double r_slow = 0.0, r_fast = 0.0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_ds4_v021(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_ds4_v021(soa_rank, soa_category, soa_weight, soa_id, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs(r_slow - r_fast) < fmax(fabs(r_slow) * 1e-6, 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    free(soa_rank);
    free(soa_category);
    free(soa_weight);
    free(soa_id);
    return 0;
}
