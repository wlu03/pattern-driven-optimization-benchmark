static void __attribute__((noinline))
is5_kernel_v011(float * __restrict__ out,const float * __restrict__ A,const float * __restrict__ B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*A[i]+B[i]*2.0f-A[i]*0.5f+B[i]*B[i];
}

void fast_is5_v011(float *out,float *A,float *B,int n){
    int ok=(out+n<=A||A+n<=out)&&(out+n<=B||B+n<=out);
    if(ok) is5_kernel_v011(out,A,B,n);
    else for(int i=0;i<n;i++) out[i]=A[i]*A[i]+B[i]*2.0f-A[i]*0.5f+B[i]*B[i];
}