#include <math.h>
double is2_expensive_v001(double val, double thr);

void slow_is2_v001(double *out,double *in,int n,double thr){
    for(int i=0;i<n;i++){
        out[i]=is2_expensive_v001(in[i],thr);
    }
}