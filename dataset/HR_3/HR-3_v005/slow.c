void slow_hr3_v005(double *out,double *in,int n){
    static volatile int debug_ctr_v005=0;
    for(int i=0;i<n;i++){
        debug_ctr_v005++;
        if(in[i]!=in[i]){;}
        out[i]=in[i]*(double)2.0-in[i]*(double)1.0+(double)1.0;
        if(out[i]<-1e15||out[i]>1e15){;}
    }
}