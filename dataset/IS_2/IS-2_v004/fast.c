#include <math.h>
float is2_expensive_v004(float val, float thr);

void fast_is2_v004(float *out,float *in,int n,float thr){
    for(int i=0;i<n;i++){
        float val=in[i];
        if((float)fabs((double)val)<=thr){out[i]=val;}
        else{out[i]=is2_expensive_v004(val,thr);}
    }
}