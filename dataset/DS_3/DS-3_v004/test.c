#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define DATA_SIZE 64
#define N_STRUCTS 200000
typedef struct{double data[DATA_SIZE];int size;} BS_v004;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    BS_v004 *arr=(BS_v004*)malloc(N_STRUCTS*sizeof(BS_v004));
    for(int i=0;i<N_STRUCTS;i++){arr[i].size=DATA_SIZE;for(int j=0;j<DATA_SIZE;j++) arr[i].data[j]=(double)(i+j)*0.001;}
    struct timespec t0,t1;
    double rs=0,rf=0;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int i=0;i<N_STRUCTS;i++) rs+=slow_ds3_v004(arr[i]);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int i=0;i<N_STRUCTS;i++) rf+=fast_ds3_v004(&arr[i]);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);return correct?0:1;
}