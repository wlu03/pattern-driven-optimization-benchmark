#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v024(float *X, float *Y, int n, float *sum_x, float *sumsq_x, float *sum_y, float *sumsq_y) {
    { float s=0; for(int i=0;i<n;i++) s+=X[i]; *sum_x=s; }
    { float s=0; for(int i=0;i<n;i++) s+=X[i]*X[i]; *sumsq_x=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]; *sum_y=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]*Y[i]; *sumsq_y=s; }
}