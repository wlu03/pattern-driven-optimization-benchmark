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

#define N 50000
#define M 50000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(456);
    int *arr=(int*)malloc(N*sizeof(int));
    int *queries=(int*)malloc(M*sizeof(int));
    for(int i=0;i<N;i++) arr[i]=i*3+1;
    for(int q=0;q<M;q++) queries[q]=(rand()%N)*3+1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_comp_v060(arr,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_comp_v060(arr,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);free(queries);return correct?0:1;
}