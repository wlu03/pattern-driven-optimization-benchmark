void fast_hr3_v008(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*(float)3.0+(float)2.5;
}