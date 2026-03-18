#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v019(float *X, float *Y, float *Z, int n, float *mean_x, float *var_x, float *mean_y, float *var_y, float *mean_z, float *var_z) {
    float sX=0; float sY=0; float sZ=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sY+=Y[i]; sZ+=Z[i]; }
    *mean_x=sX/n; *mean_y=sY/n; *mean_z=sZ/n;
    float vX=0; float vY=0; float vZ=0; float mX=*mean_x; float mY=*mean_y; float mZ=*mean_z;
    for(int i=0;i<n;i++) { { float d=X[i]-mX; vX+=d*d; } { float d=Y[i]-mY; vY+=d*d; } { float d=Z[i]-mZ; vZ+=d*d; } }
    *var_x=vX/n; *var_y=vY/n; *var_z=vZ/n;
}