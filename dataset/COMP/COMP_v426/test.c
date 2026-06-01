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
typedef struct { float a, b, cold0,cold1,cold2,cold3,cold4,cold5,cold6,cold7,cold8,cold9,cold10,cold11,cold12,cold13,cold14,cold15,cold16,cold17,cold18,cold19,cold20,cold21,cold22,cold23,cold24,cold25,cold26,cold27,cold28,cold29; } Wide_v426;
typedef struct { float a, b; } Hot_v426;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    Wide_v426 *w=(Wide_v426*)malloc(N*sizeof(Wide_v426));
    Hot_v426 *h=(Hot_v426*)malloc(N*sizeof(Hot_v426));
    for(int i=0;i<N;i++){
        w[i].a=(float)((i%100)+1)*0.01f;
        w[i].b=(float)((i%50)+1)*0.02f;
        h[i].a=w[i].a;
        h[i].b=w[i].b;
    }
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v426(w,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v426(h,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(w);free(h);return correct?0:1;
}