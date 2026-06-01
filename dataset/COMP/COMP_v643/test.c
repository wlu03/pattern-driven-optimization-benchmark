#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
/* ── standardized correctness check (auto-injected) ─────────────────── */
static inline int _bench_close(double a, double b, double atol, double rtol) {
    double d = a - b; if (d < 0) d = -d;
    double mb = b; if (mb < 0) mb = -mb;
    return d <= atol + rtol * mb;
}
/* ── end ────────────────────────────────────────────────────────────── */

#define N 4000
#define M 4000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(123);
    int *keys=(int*)malloc(N*sizeof(int));
    float *vals=(float*)malloc(N*sizeof(float));
    int *queries=(int*)malloc(M*sizeof(int));
    for(int i=0;i<N;i++){keys[i]=i*7+3;vals[i]=(float)(i%100)*0.5f;}
    for(int q=0;q<M;q++){queries[q]=(rand()%N)*7+3;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v643(keys,vals,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v643(keys,vals,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys);free(vals);free(queries);return correct?0:1;
}