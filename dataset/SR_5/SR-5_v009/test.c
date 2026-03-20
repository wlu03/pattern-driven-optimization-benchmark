#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 1000000
#define M 128

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *data=malloc(N*sizeof(double)),*os=malloc(N*sizeof(double)),*of=malloc(N*sizeof(double)),*w=malloc(M*sizeof(double));
    for(int i=0;i<N;i++) data[i]=(double)((i%100)+1)*0.01;
    for(int i=0;i<M;i++) w[i]=(double)((i%10)+1)*0.1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_sr5_v009(os,data,N,w,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_sr5_v009(of,data,N,w,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++){double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>1e-7*(r+1e-12)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(data);free(os);free(of);free(w);return correct?0:1;
}