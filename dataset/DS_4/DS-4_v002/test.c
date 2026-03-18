#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v002;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 5000000;
    AoS_v002 *arr = malloc(n * sizeof(AoS_v002));
    double *soa_ny = malloc(5000000 * sizeof(double));
    double *soa_nx = malloc(5000000 * sizeof(double));
    double *soa_px = malloc(5000000 * sizeof(double));
    for (int i = 0; i < 5000000; i++) {
        int iv = (i % 997) + 1;
        double dv = (double)iv * 0.001;
        arr[i].ny = dv * 1;
        arr[i].nx = dv * 2;
        arr[i].px = dv * 3;
        soa_ny[i] = (double)(dv * 1);
        soa_nx[i] = (double)(dv * 2);
        soa_px[i] = (double)(dv * 3);
    }
    double r_slow = 0.0, r_fast = 0.0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_ds4_v002(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_ds4_v002(soa_ny, soa_nx, soa_px, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs(r_slow - r_fast) < fmax(fabs(r_slow) * 1e-6, 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    free(soa_ny);
    free(soa_nx);
    free(soa_px);
    return 0;
}
