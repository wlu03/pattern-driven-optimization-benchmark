#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_ITEMS 5000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *items=malloc(N_ITEMS*sizeof(float)),*as=malloc(N_ITEMS*sizeof(float)),*af=malloc(N_ITEMS*sizeof(float));
    srand(42);
    for(int i=0;i<N_ITEMS;i++) items[i]=(float)(rand()%10000)*0.001f;
    int szs=0,szf=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_al2_v011(as,&szs,items,N_ITEMS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_al2_v011(af,&szf,items,N_ITEMS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=(szs==szf);
    for(int i=0;i<szs&&correct;i++){double d=fabs((double)(as[i]-af[i]));if(d>1e-5){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(items);free(as);free(af);return correct?0:1;
}