#include <math.h>
double is2_expensive_v009(double val, double thr);

void fast_is2_v009(double *out,double *in,int n,double thr){
    for(int i=0;i<n;i++){
        double val=in[i];
        if((double)fabs((double)val)<=thr){out[i]=val;}
        else{out[i]=is2_expensive_v009(val,thr);}
    }
}