#include <math.h>
static double norm_v012(double *w,int m){
    double s=0;
    for(int j=0;j<m;j++) s+=w[j]*w[j];
    return (double)sqrt((double)s);
}

void fast_sr5_v012(double *out,double *data,int n,double *w,int m){
    double inv=(double)1.0/norm_v012(w,m);
    for(int i=0;i<n;i++) out[i]=data[i]*inv;
}