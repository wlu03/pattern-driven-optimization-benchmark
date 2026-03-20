#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 5000000
#define REPS 5

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *A=malloc(N*sizeof(float)),*B=malloc(N*sizeof(float)),*os=malloc(N*sizeof(float)),*of=malloc(N*sizeof(float));
    for(int i=0;i<N;i++){A[i]=(float)((i%100)+1)*0.01f;B[i]=(float)((i%50)+1)*0.02f;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_mi2_v005(os,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_mi2_v005(of,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){double d=fabs((double)(os[i]-of[i]));if(d>1e-5){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}