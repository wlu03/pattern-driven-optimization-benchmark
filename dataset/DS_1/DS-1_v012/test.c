#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N_KEYS 5000
#define N_Q 10000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *keys=malloc(N_KEYS*sizeof(int)),*vals=malloc(N_KEYS*sizeof(int)),*queries=malloc(N_Q*sizeof(int));
    for(int i=0;i<N_KEYS;i++){keys[i]=i*7+13;vals[i]=i*3+1;}
    srand(42);
    for(int i=0;i<N_Q;i++) queries[i]=keys[rand()%N_KEYS];
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_ds1_v012(keys,vals,N_KEYS,queries,N_Q); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_ds1_v012(keys,vals,N_KEYS,queries,N_Q); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=(rs==rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys);free(vals);free(queries);return correct?0:1;
}