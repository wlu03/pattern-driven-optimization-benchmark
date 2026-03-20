__attribute__((noinline))
void slow_is5_v006(double *out,double *A,double *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*A[i]+B[i]*2.0-A[i]*0.5+B[i]*B[i];
}