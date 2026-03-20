void fast_cf4_v011(double *out,double *in,int n,int tag){
    if(tag==0){for(int i=0;i<n;i++) out[i]=in[i]>0.0?in[i]:0.0;}
    else if(tag==1){for(int i=0;i<n;i++) out[i]=in[i]*in[i];}
    else{for(int i=0;i<n;i++) out[i]=in[i]*1.5;}
}