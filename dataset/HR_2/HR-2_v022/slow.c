#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v022(float *X, float *Y, float *Z, int n, float *sum_x, float *sumsq_x, float *sum_y, float *sumsq_y, float *sum_z, float *sumsq_z) {
    { float s=0; for(int i=0;i<n;i++) s+=X[i]; *sum_x=s; }
    { float s=0; for(int i=0;i<n;i++) s+=X[i]*X[i]; *sumsq_x=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]; *sum_y=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]*Y[i]; *sumsq_y=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Z[i]; *sum_z=s; }
    { float s=0; for(int i=0;i<n;i++) s+=Z[i]*Z[i]; *sumsq_z=s; }
}