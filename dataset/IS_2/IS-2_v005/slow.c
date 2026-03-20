#include <math.h>
float is2_expensive_v005(float val, float thr);

void slow_is2_v005(float *out,float *in,int n,float thr){
    for(int i=0;i<n;i++){
        out[i]=is2_expensive_v005(in[i],thr);
    }
}