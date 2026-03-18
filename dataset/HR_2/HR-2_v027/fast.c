#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v027(float *X, float *Y, float *Z, int n, float *sum_x, float *sumsq_x, float *sum_y, float *sumsq_y, float *sum_z, float *sumsq_z) {
    float sX=0, sqX=0; float sY=0, sqY=0; float sZ=0, sqZ=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sqX+=X[i]*X[i]; sY+=Y[i]; sqY+=Y[i]*Y[i]; sZ+=Z[i]; sqZ+=Z[i]*Z[i]; }
    *sum_x=sX; *sumsq_x=sqX; *sum_y=sY; *sumsq_y=sqY; *sum_z=sZ; *sumsq_z=sqZ;
}