#include <math.h>
static double norm_v004(double *w,int m){
    double s=0;
    for(int j=0;j<m;j++) s+=(double)fabs((double)w[j]);
    return s;
}

void fast_sr5_v004(double *out,double *data,int n,double *w,int m){
    double inv=(double)1.0/norm_v004(w,m);
    for(int i=0;i<n;i++) out[i]=data[i]*inv;
}