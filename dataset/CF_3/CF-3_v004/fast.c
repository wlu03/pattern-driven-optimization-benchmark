void fast_cf3_v004(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]+in[i]*0.25f+1.0f;
}