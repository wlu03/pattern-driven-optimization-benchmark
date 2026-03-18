#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *X = malloc(N * sizeof(float)); for(int i=0;i<N;i++) X[i]=(float)(i%100+1)*0.1f;
    float *Y = malloc(N * sizeof(float)); for(int i=0;i<N;i++) Y[i]=(float)(i%100+1)*0.1f;
    float *Z = malloc(N * sizeof(float)); for(int i=0;i<N;i++) Z[i]=(float)(i%100+1)*0.1f;
    float mn_s_x=0, mx_s_x=0; float mn_s_y=0, mx_s_y=0; float mn_s_z=0, mx_s_z=0;
    float mn_f_x=0, mx_f_x=0; float mn_f_y=0, mx_f_y=0; float mn_f_z=0, mx_f_z=0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_hr2_v009(X, Y, Z, N, &mn_s_x, &mx_s_x, &mn_s_y, &mx_s_y, &mn_s_z, &mx_s_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_hr2_v009(X, Y, Z, N, &mn_f_x, &mx_f_x, &mn_f_y, &mx_f_y, &mn_f_z, &mx_f_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(mn_s_x-mn_f_x))<1e-9 && fabs((double)(mx_s_x-mx_f_x))<1e-9 && fabs((double)(mn_s_y-mn_f_y))<1e-9 && fabs((double)(mx_s_y-mx_f_y))<1e-9 && fabs((double)(mn_s_z-mn_f_z))<1e-9 && fabs((double)(mx_s_z-mx_f_z))<1e-9) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y); free(Z);
    return 0;
}