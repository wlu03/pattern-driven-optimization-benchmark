static float __attribute__((noinline)) cf4_fn0_v013(float x){return x>0.0f?x:0.0f;}
static float __attribute__((noinline)) cf4_fn1_v013(float x){return x*x;}
static float __attribute__((noinline)) cf4_fn2_v013(float x){return x*1.5f;}

void slow_cf4_v013(float *out,float *in,int n,int tag){
    for(int i=0;i<n;i++){
        if(tag==0) out[i]=cf4_fn0_v013(in[i]);
        else if(tag==1) out[i]=cf4_fn1_v013(in[i]);
        else out[i]=cf4_fn2_v013(in[i]);
    }
}