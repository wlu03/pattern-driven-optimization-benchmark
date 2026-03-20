#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *A = malloc(N * sizeof(float));
    float *B = malloc(N * sizeof(float));
    srand(42);
    for (int i = 0; i < N; i++) {
        A[i] = (rand() % 100 < 95) ? 0.0f : (float)(rand() % 10 + 1) * 0.1f;
        B[i] = (rand() % 100 < 95) ? 0.0f : (float)(rand() % 10 + 1) * 0.1f;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_slow = slow_is1_v008(A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    float r_fast = fast_is1_v008(A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}