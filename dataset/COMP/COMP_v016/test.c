#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 200000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *X=malloc(N*sizeof(float)),*Y=malloc(N*sizeof(float));
    for(int i=0;i<N;i++){X[i]=(float)((i%200)-100)*0.01f;Y[i]=(float)((i%100)-50)*0.02f;}
    float alpha=(float)2.5f,beta=(float)1.5f;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v016(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v016(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(X);free(Y);return correct?0:1;
}