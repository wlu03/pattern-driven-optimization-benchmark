#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 5000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *X = malloc(N * sizeof(double)); for(int i=0;i<N;i++) X[i]=(double)(i%100+1)*0.1;
    double *Y = malloc(N * sizeof(double)); for(int i=0;i<N;i++) Y[i]=(double)(i%100+1)*0.1;
    double *Z = malloc(N * sizeof(double)); for(int i=0;i<N;i++) Z[i]=(double)(i%100+1)*0.1;
    double su_s_x=0, sq_s_x=0; double su_s_y=0, sq_s_y=0; double su_s_z=0, sq_s_z=0;
    double su_f_x=0, sq_f_x=0; double su_f_y=0, sq_f_y=0; double su_f_z=0, sq_f_z=0;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_hr2_v016(X, Y, Z, N, &su_s_x, &sq_s_x, &su_s_y, &sq_s_y, &su_s_z, &sq_s_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_hr2_v016(X, Y, Z, N, &su_f_x, &sq_f_x, &su_f_y, &sq_f_y, &su_f_z, &sq_f_z);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(su_s_x-su_f_x))<1e-4 && fabs((double)(sq_s_x-sq_f_x))<1e-4 && fabs((double)(su_s_y-su_f_y))<1e-4 && fabs((double)(sq_s_y-sq_f_y))<1e-4 && fabs((double)(su_s_z-su_f_z))<1e-4 && fabs((double)(sq_s_z-sq_f_z))<1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y); free(Z);
    return 0;
}