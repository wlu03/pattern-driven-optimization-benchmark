void fast_hr3_v002(double *out,double *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*(double)3.0-in[i]*(double)1.0+(double)1.0;
}