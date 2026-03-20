__attribute__((noinline))
void slow_is5_v011(float *out,float *A,float *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*A[i]+B[i]*2.0f-A[i]*0.5f+B[i]*B[i];
}