void slow_mi2_v010(float *out,float *A,float *B,int n){
    memset(out,0,n*sizeof(float));
    for(int i=0;i<n;i++) out[i]=A[i]+B[i];
}