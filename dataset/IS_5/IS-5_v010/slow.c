__attribute__((noinline))
void slow_is5_v010(float *out,float *A,float *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*1.5f+B[i]*2.5f-A[i]*B[i]*0.1f;
}