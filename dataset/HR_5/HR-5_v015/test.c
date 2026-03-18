#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 20000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A = malloc(N * sizeof(double)); for(int i=0;i<N;i++) A[i]=(double)(i%100+1)*0.1;
    double *B = malloc(N * sizeof(double)); for(int i=0;i<N;i++) B[i]=(double)(i%50+1)*0.1;
    double *out_slow = calloc(N, sizeof(double));
    double *out_fast = calloc(N, sizeof(double));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++) slow_hr5_v015(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++) fast_hr5_v015(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    int correct = 1;
    for (int i = 0; i < N; i++) if (fabs(out_slow[i] - out_fast[i]) > 1e-9) { correct = 0; break; }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}