static void __attribute__((noinline))
is5_kernel_v010(float * __restrict__ out,const float * __restrict__ A,const float * __restrict__ B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*1.5f+B[i]*2.5f-A[i]*B[i]*0.1f;
}

void fast_is5_v010(float *out,float *A,float *B,int n){
    int ok=(out+n<=A||A+n<=out)&&(out+n<=B||B+n<=out);
    if(ok) is5_kernel_v010(out,A,B,n);
    else for(int i=0;i<n;i++) out[i]=A[i]*1.5f+B[i]*2.5f-A[i]*B[i]*0.1f;
}