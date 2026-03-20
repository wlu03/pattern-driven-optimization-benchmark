#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 80000000
#define REPS 3

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *A=malloc(N*sizeof(double)),*B=malloc(N*sizeof(double)),*os=malloc(N*sizeof(double)),*of=malloc(N*sizeof(double));
    for(int i=0;i<N;i++){A[i]=(double)((i%100)+1)*0.1;B[i]=(double)((i%50)+1)*0.05;}
    volatile double sink_slow=0, sink_fast=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) sink_slow+=slow_is5_v000(os,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) sink_fast+=fast_is5_v000(of,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){double d=fabs((double)(os[i]-of[i])),ref=fabs((double)os[i])+fabs((double)of[i]);if(d>1e-4*(ref+1.0)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f sink=%.1f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001),(double)(sink_slow+sink_fast));
    free(A);free(B);free(os);free(of);return correct?0:1;
}