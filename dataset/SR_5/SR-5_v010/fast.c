#include <math.h>
static float norm_v010(float *w,int m){
    float s=0;
    for(int j=0;j<m;j++) s+=(float)fabs((double)w[j]);
    return s;
}

void fast_sr5_v010(float *out,float *data,int n,float *w,int m){
    float inv=(float)1.0/norm_v010(w,m);
    for(int i=0;i<n;i++) out[i]=data[i]*inv;
}