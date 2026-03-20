__attribute__((noinline))
void slow_is5_v012(double *out,double *A,double *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*1.5+B[i]*2.5-A[i]*B[i]*0.1;
}