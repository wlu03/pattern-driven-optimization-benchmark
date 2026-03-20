#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 2000000
#define REPS 3

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    float *X=malloc(N*sizeof(float)),*Y=malloc(N*sizeof(float));
    for(int i=0;i<N;i++){X[i]=(float)((i%200)-100)*0.05f;Y[i]=(float)((i%150)-75)*0.03f;}
    float mxs,mys,vxs,vys,mxf,myf,vxf,vyf;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_hr2_v014(X,Y,N,&mxs,&mys,&vxs,&vys);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_hr2_v014(X,Y,N,&mxf,&myf,&vxf,&vyf);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    double ref=fabs((double)mxs)+1e-12;
    int correct=fabs((double)(mxs-mxf))<1e-3*ref&&fabs((double)(mys-myf))<1e-3*(fabs((double)mys)+1e-12)
        &&fabs((double)(vxs-vxf))<1e-3*(fabs((double)vxs)+1e-12)&&fabs((double)(vys-vyf))<1e-3*(fabs((double)vys)+1e-12);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(X);free(Y);return correct?0:1;
}