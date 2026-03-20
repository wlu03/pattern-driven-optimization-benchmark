static double __attribute__((noinline)) cf4_fn0_v002(double x){return x>0.0?x:0.0;}
static double __attribute__((noinline)) cf4_fn1_v002(double x){return x*x;}
static double __attribute__((noinline)) cf4_fn2_v002(double x){return x*1.5;}

void slow_cf4_v002(double *out,double *in,int n,int tag){
    for(int i=0;i<n;i++){
        if(tag==0) out[i]=cf4_fn0_v002(in[i]);
        else if(tag==1) out[i]=cf4_fn1_v002(in[i]);
        else out[i]=cf4_fn2_v002(in[i]);
    }
}