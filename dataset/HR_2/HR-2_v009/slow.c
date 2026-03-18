#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr2_v009(double *X, double *Y, double *Z, int n, double *mean_x, double *var_x, double *mean_y, double *var_y, double *mean_z, double *var_z) {
    { double s=0; for(int i=0;i<n;i++) s+=X[i]; *mean_x=s/n; }
    { double s=0; for(int i=0;i<n;i++) s+=Y[i]; *mean_y=s/n; }
    { double s=0; for(int i=0;i<n;i++) s+=Z[i]; *mean_z=s/n; }
    { double v=0,m=*mean_x; for(int i=0;i<n;i++) { double d=X[i]-m; v+=d*d; } *var_x=v/n; }
    { double v=0,m=*mean_y; for(int i=0;i<n;i++) { double d=Y[i]-m; v+=d*d; } *var_y=v/n; }
    { double v=0,m=*mean_z; for(int i=0;i<n;i++) { double d=Z[i]-m; v+=d*d; } *var_z=v/n; }
}