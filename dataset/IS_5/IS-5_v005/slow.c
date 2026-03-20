__attribute__((noinline))
void slow_is5_v005(double *out,double *A,double *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5+1.0;
}