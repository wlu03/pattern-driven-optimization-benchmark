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
typedef struct { float val, weight, p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24,p25,p26,p27,p28,p29; } R_v472;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(202);
    R_v472 *aos=(R_v472*)calloc(N,sizeof(R_v472));
    float *val=(float*)calloc(N,sizeof(float));
    float *weight=(float*)malloc(N*sizeof(float));
    /* ~10% non-zero */
    for(int i=0;i<N;i++){
        weight[i]=(float)((i%50)+1)*0.02f;
        aos[i].weight=weight[i];
        if (rand()%100<10){
            aos[i].val=(float)((i%100)+1)*0.1f;
            val[i]=aos[i].val;
        }
    }
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rs=slow_comp_v472(aos,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); float rf=fast_comp_v472(val,weight,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-3*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(aos);free(val);free(weight);return correct?0:1;
}