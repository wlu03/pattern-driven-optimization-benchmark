void fast_cf3_v009(double *out,double *in,int n){
    for(int i=0;i<n;i++) out[i]=in[i]*in[i]*in[i]+in[i]*in[i]+in[i];
}