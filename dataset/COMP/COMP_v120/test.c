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

#define N 1000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *keys_s=(int*)malloc(N*sizeof(int));
    int *keys_f=(int*)malloc(N*sizeof(int));
    float *vals=(float*)malloc(N*sizeof(float));
    /* already-sorted input — slow still sorts, fast skips */
    for(int i=0;i<N;i++){keys_s[i]=i;keys_f[i]=i;vals[i]=(float)((i%100)+1)*(float)0.01f;}
    float alpha=(float)1.5f;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v120(keys_s,vals,N,alpha); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v120(keys_f,vals,N,alpha); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys_s);free(keys_f);free(vals);return correct?0:1;
}