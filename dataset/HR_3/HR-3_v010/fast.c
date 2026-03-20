void fast_hr3_v010(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*(float)1.5+(float)2.5;
}