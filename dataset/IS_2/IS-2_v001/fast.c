#include <math.h>
void fast_is2_v001(float *out,float *in,int n,float thr){
    for(int i=0;i<n;i++){
        float val=in[i];
        if((float)fabs((double)val)<=thr){out[i]=val;}
        else{
            float sign=(val>=0)?1.0f:-1.0f,abs_val=(float)fabs((double)val);
            out[i]=sign*((float)2.0+(float)sqrt((double)(abs_val-(float)2.0)));
        }
    }
}