#include <math.h>
static float norm_v008(float *w,int m){
    float s=0;
    for(int j=0;j<m;j++) s+=w[j]*w[j];
    return (float)sqrt((double)s);
}

void fast_sr5_v008(float *out,float *data,int n,float *w,int m){
    float inv=(float)1.0/norm_v008(w,m);
    for(int i=0;i<n;i++) out[i]=data[i]*inv;
}