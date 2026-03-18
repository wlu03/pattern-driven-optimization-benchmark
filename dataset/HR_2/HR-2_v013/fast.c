#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v013(double *X, double *Y, int n, double *mean_x, double *var_x, double *mean_y, double *var_y) {
    double sX=0; double sY=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sY+=Y[i]; }
    *mean_x=sX/n; *mean_y=sY/n;
    double vX=0; double vY=0; double mX=*mean_x; double mY=*mean_y;
    for(int i=0;i<n;i++) { { double d=X[i]-mX; vX+=d*d; } { double d=Y[i]-mY; vY+=d*d; } }
    *var_x=vX/n; *var_y=vY/n;
}