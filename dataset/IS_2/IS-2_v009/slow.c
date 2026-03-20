#include <math.h>
double is2_expensive_v009(double val, double thr);

void slow_is2_v009(double *out,double *in,int n,double thr){
    for(int i=0;i<n;i++){
        out[i]=is2_expensive_v009(in[i],thr);
    }
}