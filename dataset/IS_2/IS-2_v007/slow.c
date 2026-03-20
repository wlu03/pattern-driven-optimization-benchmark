#include <math.h>
float is2_expensive_v007(float val, float thr);

void slow_is2_v007(float *out,float *in,int n,float thr){
    for(int i=0;i<n;i++){
        out[i]=is2_expensive_v007(in[i],thr);
    }
}