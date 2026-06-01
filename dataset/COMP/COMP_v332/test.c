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

#define ROWS 1000
#define COLS 1500
#define SPARSITY 5

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    srand(789);
    float *vec=(float*)malloc(ROWS*sizeof(float));
    float *mat=(float*)malloc(ROWS*COLS*sizeof(float));
    float *os=(float*)malloc(COLS*sizeof(float));
    float *of=(float*)malloc(COLS*sizeof(float));
    for(int i=0;i<ROWS;i++) vec[i]=(rand()%100<SPARSITY)?(float)((i%50)+1)*0.1f:(float)0;
    for(int i=0;i<ROWS*COLS;i++) mat[i]=(float)((i%100)+1)*0.01f;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_v332(vec,mat,os,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_v332(vec,mat,of,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int j=0;j<COLS;j++){double d=fabs((double)(os[j]-of[j])),r=fabs((double)os[j]);if(d>1e-3*(r+1e-12)){correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(vec);free(mat);free(os);free(of);return correct?0:1;
}