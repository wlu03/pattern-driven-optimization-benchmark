void fast_hr3_v007(double *out,double *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*(double)2.0+(double)0.5;
}