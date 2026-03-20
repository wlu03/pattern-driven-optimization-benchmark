void fast_cf4_v008(float *out,float *in,int n,int tag){
    if(tag==0){for(int i=0;i<n;i++) out[i]=in[i]>0.0f?in[i]:0.0f;}
    else if(tag==1){for(int i=0;i<n;i++) out[i]=in[i]*in[i];}
    else{for(int i=0;i<n;i++) out[i]=in[i]*1.5f;}
}