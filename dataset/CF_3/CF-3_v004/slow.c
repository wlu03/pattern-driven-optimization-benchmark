static float __attribute__((noinline)) cf3_guard_v004(float x){
    return x>0.0f?x*x+x*0.25f+1.0f:0.0f;
}

void slow_cf3_v004(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=cf3_guard_v004(in[i]);
}