#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v017(double *X, double *Y, int n, double *sum_x, double *sumsq_x, double *sum_y, double *sumsq_y) {
    double sX=0, sqX=0; double sY=0, sqY=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sqX+=X[i]*X[i]; sY+=Y[i]; sqY+=Y[i]*Y[i]; }
    *sum_x=sX; *sumsq_x=sqX; *sum_y=sY; *sumsq_y=sqY;
}