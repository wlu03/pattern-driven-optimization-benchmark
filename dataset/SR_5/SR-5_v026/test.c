#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 500000
#define M 256

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *data     = malloc(N * sizeof(float));
    float *out_slow = malloc(N * sizeof(float));
    float *out_fast = malloc(N * sizeof(float));
    float *w        = malloc(M * sizeof(float));
    for (int i = 0; i < N; i++) data[i] = (float)((i % 200) - 100) * 0.1f;
    for (int j = 0; j < M; j++) w[j] = (float)(j % 50 + 1) * 0.02f;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr5_v026(out_slow, data, N, w, M);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr5_v026(out_fast, data, N, w, M);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    /* expected: compute norm inline, divide each element */
    float ns = 0.0; for (int j = 0; j < M; j++) ns += w[j] * w[j];
    float norm = (float)sqrt((double)ns);
    int correct = 1;
    for (int i = 0; i < N; i++) {
        double diff = fabs((double)(out_slow[i] - data[i] / norm)) / fmax(fabs((double)(data[i] / norm)), 1e-12);
        if (diff > 1e-4) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(data); free(out_slow); free(out_fast); free(w);
    return 0;
}