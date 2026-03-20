void fast_hr3_v006(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*(float)2.0+(float)1.0;
}