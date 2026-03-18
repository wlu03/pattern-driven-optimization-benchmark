#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v029(float *X, float *Y, float *Z, int n, float *min_x, float *max_x, float *min_y, float *max_y, float *min_z, float *max_z) {
    float mnX=X[0],mxX=X[0]; float mnY=Y[0],mxY=Y[0]; float mnZ=Z[0],mxZ=Z[0];
    for(int i=1;i<n;i++) { if(X[i]<mnX) mnX=X[i]; if(X[i]>mxX) mxX=X[i]; if(Y[i]<mnY) mnY=Y[i]; if(Y[i]>mxY) mxY=Y[i]; if(Z[i]<mnZ) mnZ=Z[i]; if(Z[i]>mxZ) mxZ=Z[i]; }
    *min_x=mnX; *max_x=mxX; *min_y=mnY; *max_y=mxY; *min_z=mnZ; *max_z=mxZ;
}