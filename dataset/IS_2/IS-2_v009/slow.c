#include <math.h>
void slow_is2_v009(float *out,float *in,int n,float thr){
    for(int i=0;i<n;i++){
        float val=in[i],sign=(val>=0)?1.0f:-1.0f,abs_val=(float)fabs((double)val);
        out[i]=(abs_val>thr)?sign*((float)0.5+(float)sqrt((double)(abs_val-(float)0.5))):val;
    }
}