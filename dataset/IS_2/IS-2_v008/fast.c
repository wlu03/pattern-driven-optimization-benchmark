#include <math.h>
void fast_is2_v008(double *out,double *in,int n,double thr){
    for(int i=0;i<n;i++){
        double val=in[i];
        if((double)fabs((double)val)<=thr){out[i]=val;}
        else{
            double sign=(val>=0)?1.0:-1.0,abs_val=(double)fabs((double)val);
            out[i]=sign*((double)0.5+(double)sqrt((double)(abs_val-(double)0.5)));
        }
    }
}