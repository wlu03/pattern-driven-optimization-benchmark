#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v016(double *X, double *Y, double *Z, int n, double *sum_x, double *sumsq_x, double *sum_y, double *sumsq_y, double *sum_z, double *sumsq_z) {
    { double s=0; for(int i=0;i<n;i++) s+=X[i]; *sum_x=s; }
    { double s=0; for(int i=0;i<n;i++) s+=X[i]*X[i]; *sumsq_x=s; }
    { double s=0; for(int i=0;i<n;i++) s+=Y[i]; *sum_y=s; }
    { double s=0; for(int i=0;i<n;i++) s+=Y[i]*Y[i]; *sumsq_y=s; }
    { double s=0; for(int i=0;i<n;i++) s+=Z[i]; *sum_z=s; }
    { double s=0; for(int i=0;i<n;i++) s+=Z[i]*Z[i]; *sumsq_z=s; }
}