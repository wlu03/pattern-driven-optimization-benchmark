#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 2000000
#define REPS 5

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *in=malloc(N*sizeof(float)),*os=malloc(N*sizeof(float)),*of=malloc(N*sizeof(float));
    for(int i=0;i<N;i++) in[i]=(float)((i%200)-100)*0.05f;
    int tag=2;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_cf4_v013(os,in,N,tag);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_cf4_v013(of,in,N,tag);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){double d=fabs((double)(os[i]-of[i]));if(d>1e-6){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}