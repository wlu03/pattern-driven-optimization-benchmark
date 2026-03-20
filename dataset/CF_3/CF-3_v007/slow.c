static float __attribute__((noinline)) cf3_guard_v007(float x){
    return x>0.0f?x*x+x*0.5f:0.0f;
}

void slow_cf3_v007(float *out,float *in,int n){
    for(int i=0;i<n;i++) out[i]=cf3_guard_v007(in[i]);
}