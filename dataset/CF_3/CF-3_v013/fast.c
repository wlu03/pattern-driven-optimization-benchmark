void fast_cf3_v013(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*in[i]+in[i]*in[i]+in[i];
}