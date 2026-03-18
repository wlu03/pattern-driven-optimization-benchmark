#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v011(float *X, float *Y, int n, float *mean_x, float *var_x, float *mean_y, float *var_y) {
    { float s=0; for(int i=0;i<n;i++) s+=X[i]; *mean_x=s/n; }
    { float s=0; for(int i=0;i<n;i++) s+=Y[i]; *mean_y=s/n; }
    { float v=0,m=*mean_x; for(int i=0;i<n;i++) { float d=X[i]-m; v+=d*d; } *var_x=v/n; }
    { float v=0,m=*mean_y; for(int i=0;i<n;i++) { float d=Y[i]-m; v+=d*d; } *var_y=v/n; }
}