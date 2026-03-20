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
    float *A=malloc(total*sizeof(float)),*B=malloc(total*sizeof(float)),*os=malloc(total*sizeof(float)),*of=malloc(total*sizeof(float));
    for(int i=0;i<total;i++){A[i]=(float)((i%100)+1)*0.01f;B[i]=(float)((i%50)+1)*0.02f;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_v064(os,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_v064(of,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<total;i++){double d=fabs((double)(os[i]-of[i]));if(d>1e-6){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}