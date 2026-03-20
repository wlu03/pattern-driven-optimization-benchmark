void slow_hr3_v004(float *out,float *in,int n){
    static volatile int debug_ctr_v004=0;
    for(int i=0;i<n;i++){
        debug_ctr_v004++;
        if(in[i]!=in[i]){;}
        out[i]=in[i]*(float)2.0+(float)1.0;
        if(out[i]<-1e15||out[i]>1e15){;}
    }
}