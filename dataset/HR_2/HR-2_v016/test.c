#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *X = malloc(N * sizeof(float)); for(int i=0;i<N;i++) X[i]=(float)(i%100+1)*0.1f;
    float *Y = malloc(N * sizeof(float)); for(int i=0;i<N;i++) Y[i]=(float)(i%100+1)*0.1f;
    float ms_x=0, vs_x=0; float ms_y=0, vs_y=0;
    float mf_x=0, vf_x=0; float mf_y=0, vf_y=0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_hr2_v016(X, Y, N, &ms_x, &vs_x, &ms_y, &vs_y);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_hr2_v016(X, Y, N, &mf_x, &vf_x, &mf_y, &vf_y);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(ms_x-mf_x))<1e-4 && fabs((double)(vs_x-vf_x))<1e-4 && fabs((double)(ms_y-mf_y))<1e-4 && fabs((double)(vs_y-vf_y))<1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y);
    return 0;
}