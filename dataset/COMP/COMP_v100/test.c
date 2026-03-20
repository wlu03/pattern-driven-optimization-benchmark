#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS 2000
#define COLS 2500

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int total=ROWS*COLS;
    double *A=malloc(total*sizeof(double)),*B=malloc(total*sizeof(double)),*os=malloc(total*sizeof(double)),*of=malloc(total*sizeof(double));
    for(int i=0;i<total;i++){A[i]=(double)((i%100)+1)*0.01;B[i]=(double)((i%50)+1)*0.02;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_v100(os,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_v100(of,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<total;i++){double d=fabs((double)(os[i]-of[i]));if(d>1e-6){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}