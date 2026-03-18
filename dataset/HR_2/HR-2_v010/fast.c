#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v010(double *X, double *Y, double *Z, int n, double *mean_x, double *var_x, double *mean_y, double *var_y, double *mean_z, double *var_z) {
    double sX=0; double sY=0; double sZ=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sY+=Y[i]; sZ+=Z[i]; }
    *mean_x=sX/n; *mean_y=sY/n; *mean_z=sZ/n;
    double vX=0; double vY=0; double vZ=0; double mX=*mean_x; double mY=*mean_y; double mZ=*mean_z;
    for(int i=0;i<n;i++) { { double d=X[i]-mX; vX+=d*d; } { double d=Y[i]-mY; vY+=d*d; } { double d=Z[i]-mZ; vZ+=d*d; } }
    *var_x=vX/n; *var_y=vY/n; *var_z=vZ/n;
}