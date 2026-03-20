#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *base=malloc(N*sizeof(int)),*as=malloc(N*sizeof(int)),*af=malloc(N*sizeof(int));
    for(int i=0;i<N;i++) base[i]=i;
    srand(99);
    int swaps=N/50;
    for(int s=0;s<swaps;s++){int i=rand()%(N-1);int t=base[i];base[i]=base[i+1];base[i+1]=t;}
    memcpy(as,base,N*sizeof(int)); memcpy(af,base,N*sizeof(int));
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_is4_v010(as,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_is4_v010(af,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++) if(as[i]!=af[i]){correct=0;break;}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(base);free(as);free(af);return correct?0:1;
}