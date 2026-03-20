#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *in=malloc(N*sizeof(float)),*os=malloc(N*sizeof(float)),*of=malloc(N*sizeof(float));
    srand(42);
    for(int i=0;i<N;i++) in[i]=(rand()%100<5)?((float)(rand()%40+20)):(((float)(rand()%200)-100)*0.01f);
    float thr=(float)0.5;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_is2_v010(os,in,N,thr); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_is2_v010(of,in,N,thr); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++){double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>1e-4*(r+1e-9)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}