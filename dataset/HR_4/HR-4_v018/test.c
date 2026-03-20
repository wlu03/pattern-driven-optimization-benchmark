#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 2000000
#define REPS 10

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A=malloc(N*sizeof(double)),*B=malloc(N*sizeof(double));
    for(int i=0;i<N;i++){A[i]=(double)((i%100)+1)*0.01;B[i]=(double)((i%50)+1)*0.02;}
    struct timespec t0,t1;
    double rs=0,rf=0;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) rs=slow_hr4_v018(A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) rf=fast_hr4_v018(A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    double diff=fabs((double)(rs-rf)),ref2=fabs((double)rs)+1e-12;
    int correct=diff<1e-7*ref2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B); return correct?0:1;
}