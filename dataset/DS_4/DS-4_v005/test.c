#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    double temp;
    double humidity;
    double pressure;
    double wind_speed;
    double wind_dir;
    double light;
    double noise;
    double co2;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v005;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int n = 5000000;
    AoS_v005 *arr = malloc(n * sizeof(AoS_v005));
    double *soa_light = malloc(5000000 * sizeof(double));
    double *soa_noise = malloc(5000000 * sizeof(double));
    for (int i = 0; i < 5000000; i++) {
        int iv = (i % 997) + 1;
        double dv = (double)iv * 0.001;
        arr[i].light = dv * 1;
        arr[i].noise = dv * 2;
        soa_light[i] = (double)(dv * 1);
        soa_noise[i] = (double)(dv * 2);
    }
    double r_slow = 0.0, r_fast = 0.0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_ds4_v005(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_ds4_v005(soa_light, soa_noise, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs(r_slow - r_fast) < fmax(fabs(r_slow) * 1e-6, 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    free(soa_light);
    free(soa_noise);
    return 0;
}
