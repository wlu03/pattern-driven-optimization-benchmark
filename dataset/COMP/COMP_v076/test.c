#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS 100
#define COLS 500

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *mat=malloc(ROWS*COLS*sizeof(float)),*cs=malloc(COLS*sizeof(float)),*cf=malloc(COLS*sizeof(float));
    for(int i=0;i<ROWS*COLS;i++) mat[i]=(float)((i%100)+1)*0.01f;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_v076(mat,cs,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_v076(mat,cf,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int j=0;j<COLS;j++){double d=fabs((double)(cs[j]-cf[j])),r=fabs((double)cs[j]);if(d>1e-3*(r+1e-12)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(mat);free(cs);free(cf);return correct?0:1;
}