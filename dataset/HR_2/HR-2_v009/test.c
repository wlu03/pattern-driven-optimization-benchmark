#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *X = malloc(N * sizeof(double)); for(int i=0;i<N;i++) X[i]=(double)(i%100+1)*0.1;
    double *Y = malloc(N * sizeof(double)); for(int i=0;i<N;i++) Y[i]=(double)(i%100+1)*0.1;
    double *Z = malloc(N * sizeof(double)); for(int i=0;i<N;i++) Z[i]=(double)(i%100+1)*0.1;
    double ms_x=0, vs_x=0; double ms_y=0, vs_y=0; double ms_z=0, vs_z=0;
    double mf_x=0, vf_x=0; double mf_y=0, vf_y=0; double mf_z=0, vf_z=0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_hr2_v009(X, Y, Z, N, &ms_x, &vs_x, &ms_y, &vs_y, &ms_z, &vs_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_hr2_v009(X, Y, Z, N, &mf_x, &vf_x, &mf_y, &vf_y, &mf_z, &vf_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(ms_x-mf_x))<1e-4 && fabs((double)(vs_x-vf_x))<1e-4 && fabs((double)(ms_y-mf_y))<1e-4 && fabs((double)(vs_y-vf_y))<1e-4 && fabs((double)(ms_z-mf_z))<1e-4 && fabs((double)(vs_z-vf_z))<1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y); free(Z);
    return 0;
}