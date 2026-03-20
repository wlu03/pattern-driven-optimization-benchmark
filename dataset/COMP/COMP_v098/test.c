#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS 3000
#define COLS 3000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int total=ROWS*COLS;
    double *ms=malloc(total*sizeof(double)),*mf=malloc(total*sizeof(double));
    for(int k=0;k<total;k++) ms[k]=(double)((k%100)+1)*0.1;
    memcpy(mf,ms,total*sizeof(double));
    int mode=1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_v098(ms,ROWS,COLS,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_v098(mf,ROWS,COLS,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int k=0;k<total;k++){double d=fabs((double)(ms[k]-mf[k]));if(d>1e-6){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(ms);free(mf);return correct?0:1;
}