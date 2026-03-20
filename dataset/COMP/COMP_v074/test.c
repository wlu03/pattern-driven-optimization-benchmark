#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define ROWS 500
#define COLS 1000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int total=ROWS*COLS;
    float *A=malloc(total*sizeof(float)),*B=malloc(total*sizeof(float));
    for(int i=0;i<total;i++){A[i]=(float)((i%100)+1)*0.01f;B[i]=(float)((i%50)+1)*0.02f;}
    float base=(float)2.0f;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v074(A,B,ROWS,COLS,base); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v074(A,B,ROWS,COLS,base); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);return correct?0:1;
}