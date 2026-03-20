#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *X=malloc(N*sizeof(double)),*Y=malloc(N*sizeof(double));
    for(int i=0;i<N;i++){X[i]=(double)((i%200)-100)*0.01;Y[i]=(double)((i%100)-50)*0.02;}
    double alpha=(double)2.5,beta=(double)1.5;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rs=slow_comp_v049(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rf=fast_comp_v049(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(X);free(Y);return correct?0:1;
}