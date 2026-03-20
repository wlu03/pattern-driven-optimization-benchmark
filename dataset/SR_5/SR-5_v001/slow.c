#include <math.h>
static float norm_v001(float *w,int m){
    float s=0;
    for(int j=0;j<m;j++) s+=(float)fabs((double)w[j]);
    return s;
}

void slow_sr5_v001(float *out,float *data,int n,float *w,int m){
    for(int i=0;i<n;i++) out[i]=data[i]/norm_v001(w,m);
}