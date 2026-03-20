void slow_hr3_v009(double *out,double *in,int n){
    static volatile int debug_ctr_v009=0;
    for(int i=0;i<n;i++){
        debug_ctr_v009++;
        if(in[i]!=in[i]){;}
        out[i]=in[i]*in[i]*(double)3.0+(double)0.5;
        if(out[i]<-1e15||out[i]>1e15){;}
    }
}