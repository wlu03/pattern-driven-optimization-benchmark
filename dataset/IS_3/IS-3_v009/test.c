#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 10000000
#define REPS 20

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    double *arr=malloc(N*sizeof(double));
    srand(42);
    for(int i=0;i<N;i++) arr[i]=(double)(rand()%100)*0.1;
    arr[10]=(double)100.0+1.0;
    double thr=(double)100.0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    volatile int rs=0; for(int r=0;r<REPS;r++) rs=slow_is3_v009(arr,N,thr);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    volatile int rf=0; for(int r=0;r<REPS;r++) rf=fast_is3_v009(arr,N,thr);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=(slow_is3_v009(arr,N,thr)==fast_is3_v009(arr,N,thr));
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr); return correct?0:1;
}