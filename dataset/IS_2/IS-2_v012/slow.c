#include <math.h>
void slow_is2_v012(double *out,double *in,int n,double thr){
    for(int i=0;i<n;i++){
        double val=in[i],sign=(val>=0)?1.0:-1.0,abs_val=(double)fabs((double)val);
        out[i]=(abs_val>thr)?sign*((double)2.0*(1.0+(double)exp((double)(abs_val-(double)2.0)-1.0))):val;
    }
}