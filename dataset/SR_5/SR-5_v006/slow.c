#include <math.h>
static double norm_v006(double *w,int m){
    double s=0;
    for(int j=0;j<m;j++) s+=(double)fabs((double)w[j]);
    return s;
}

void slow_sr5_v006(double *out,double *data,int n,double *w,int m){
    for(int i=0;i<n;i++) out[i]=data[i]/norm_v006(w,m);
}