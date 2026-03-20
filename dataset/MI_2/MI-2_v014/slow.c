void slow_mi2_v014(double *out,double *A,double *B,int n){
    memset(out,0,n*sizeof(double));
    for(int i=0;i<n;i++) out[i]=A[i]*B[i]+(double)1.0;
}