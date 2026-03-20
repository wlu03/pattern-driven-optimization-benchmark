void slow_hr3_v014(float *out,float *in,int n){
    static volatile int debug_ctr_v014=0;
    for(int i=0;i<n;i++){
        debug_ctr_v014++;
        if(in[i]!=in[i]){;}
        out[i]=in[i]*in[i]*(float)1.5+(float)0.5;
        if(out[i]<-1e15||out[i]>1e15){;}
    }
}