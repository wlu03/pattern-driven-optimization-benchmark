#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000
#define CHUNK 8
#define N_RES 1250001

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *input=malloc(N*sizeof(double)),*rs=malloc(N_RES*sizeof(double)),*rf=malloc(N_RES*sizeof(double));
    for(int i=0;i<N;i++) input[i]=(double)((i%100)+1)*0.1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_ds2_v004(rs,input,N,CHUNK); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_ds2_v004(rf,input,N,CHUNK); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N_RES;i++){double d=fabs((double)(rs[i]-rf[i])),r=fabs((double)rs[i]);if(d>1e-8*(r+1e-12)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(input);free(rs);free(rf);return correct?0:1;
}