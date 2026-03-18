#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr2_v007(float *X, float *Y, int n, float *mean_x, float *var_x, float *mean_y, float *var_y) {
    float sX=0; float sY=0;
    for(int i=0;i<n;i++) { sX+=X[i]; sY+=Y[i]; }
    *mean_x=sX/n; *mean_y=sY/n;
    float vX=0; float vY=0; float mX=*mean_x; float mY=*mean_y;
    for(int i=0;i<n;i++) { { float d=X[i]-mX; vX+=d*d; } { float d=Y[i]-mY; vY+=d*d; } }
    *var_x=vX/n; *var_y=vY/n;
}