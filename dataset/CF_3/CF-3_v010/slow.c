static double __attribute__((noinline)) cf3_guard_v010(double x){
    return x>0.0?x*x+x*0.25+1.0:0.0;
}

void slow_cf3_v010(double *out,double *in,int n){
    for(int i=0;i<n;i++) out[i]=cf3_guard_v010(in[i]);
}