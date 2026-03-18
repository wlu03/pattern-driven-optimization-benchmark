#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v022(float *X, float *Y, float *Z, int n, float *mean_x, float *var_x, float *mean_y, float *var_y, float *mean_z, float *var_z) {
    { float s=0; for(int i=0;i<n;i++) s+=X[i]; *mean_x=s/n; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]; *mean_y=s/n; }
    { float s=0; for(int i=0;i<n;i++) s+=Z[i]; *mean_z=s/n; }
    { float v=0,m=*mean_x; for(int i=0;i<n;i++) { float d=X[i]-m; v+=d*d; } *var_x=v/n; }
    { float v=0,m=*mean_y; for(int i=0;i<n;i++) { float d=Y[i]-m; v+=d*d; } *var_y=v/n; }
    { float v=0,m=*mean_z; for(int i=0;i<n;i++) { float d=Z[i]-m; v+=d*d; } *var_z=v/n; }
}