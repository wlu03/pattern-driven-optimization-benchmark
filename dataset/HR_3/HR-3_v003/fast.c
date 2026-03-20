void fast_hr3_v003(double *out,double *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*(double)2.0+(double)2.5;
}