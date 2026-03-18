#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v009(float *X, float *Y, float *Z, int n, float *min_x, float *max_x, float *min_y, float *max_y, float *min_z, float *max_z) {
    { float mn=X[0],mx=X[0]; for(int i=1;i<n;i++) { if(X[i]<mn) mn=X[i]; if(X[i]>mx) mx=X[i]; } *min_x=mn; *max_x=mx; }
    { float mn=Y[0],mx=Y[0]; for(int i=1;i<n;i++) { if(Y[i]<mn) mn=Y[i]; if(Y[i]>mx) mx=Y[i]; } *min_y=mn; *max_y=mx; }
    { float mn=Z[0],mx=Z[0]; for(int i=1;i<n;i++) { if(Z[i]<mn) mn=Z[i]; if(Z[i]>mx) mx=Z[i]; } *min_z=mn; *max_z=mx; }
}