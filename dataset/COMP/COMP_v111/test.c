#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *A=malloc(N*sizeof(int));
    for(int i=0;i<N;i++) A[i]=(int)((i%100)+1)*0.01;
    int base=(int)1.5; int mode=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_comp_v111(A,N,base,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_comp_v111(A,N,base,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);return correct?0:1;
}