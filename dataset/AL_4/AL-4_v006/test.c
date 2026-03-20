#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define GRID_R 17
#define GRID_C 16
#define FAST_REPS 100000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); long long rs=slow_al4_v006(GRID_R,GRID_C); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    long long rf=0; for(int rep=0;rep<FAST_REPS;rep++) rf=fast_al4_v006(GRID_R,GRID_C);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/FAST_REPS;
    int correct=(rs==rf);
    printf("slow_ms=%.4f fast_ms=%.6f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    return correct?0:1;
}