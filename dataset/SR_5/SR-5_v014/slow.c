#include <math.h>
static float norm_v014(float *w,int m){
    float s=0;
    for(int j=0;j<m;j++) s+=(float)fabs((double)w[j]);
    return s;
}

void slow_sr5_v014(float *out,float *data,int n,float *w,int m){
    for(int i=0;i<n;i++) out[i]=data[i]/norm_v014(w,m);
}