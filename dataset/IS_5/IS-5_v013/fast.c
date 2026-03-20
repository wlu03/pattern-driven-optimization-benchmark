static void __attribute__((noinline))
is5_kernel_v013(double * __restrict__ out,const double * __restrict__ A,const double * __restrict__ B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5+1.0;
}

void fast_is5_v013(double *out,double *A,double *B,int n){
    int ok=(out+n<=A||A+n<=out)&&(out+n<=B||B+n<=out);
    if(ok) is5_kernel_v013(out,A,B,n);
    else for(int i=0;i<n;i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5+1.0;
}