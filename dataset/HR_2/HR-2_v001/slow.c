#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v001(double *X, double *Y, double *Z, int n, double *min_x, double *max_x, double *min_y, double *max_y, double *min_z, double *max_z) {
    { double mn=X[0],mx=X[0]; for(int i=1;i<n;i++) { if(X[i]<mn) mn=X[i]; if(X[i]>mx) mx=X[i]; } *min_x=mn; *max_x=mx; }
    { double mn=Y[0],mx=Y[0]; for(int i=1;i<n;i++) { if(Y[i]<mn) mn=Y[i]; if(Y[i]>mx) mx=Y[i]; } *min_y=mn; *max_y=mx; }
    { double mn=Z[0],mx=Z[0]; for(int i=1;i<n;i++) { if(Z[i]<mn) mn=Z[i]; if(Z[i]>mx) mx=Z[i]; } *min_z=mn; *max_z=mx; }
}