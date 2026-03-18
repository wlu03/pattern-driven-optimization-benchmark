#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v018(double *X, double *Y, double *Z, int n, double *min_x, double *max_x, double *min_y, double *max_y, double *min_z, double *max_z) {
    double mnX=X[0],mxX=X[0]; double mnY=Y[0],mxY=Y[0]; double mnZ=Z[0],mxZ=Z[0];
    for(int i=1;i<n;i++) { if(X[i]<mnX) mnX=X[i]; if(X[i]>mxX) mxX=X[i]; if(Y[i]<mnY) mnY=Y[i]; if(Y[i]>mxY) mxY=Y[i]; if(Z[i]<mnZ) mnZ=Z[i]; if(Z[i]>mxZ) mxZ=Z[i]; }
    *min_x=mnX; *max_x=mxX; *min_y=mnY; *max_y=mxY; *min_z=mnZ; *max_z=mxZ;
}