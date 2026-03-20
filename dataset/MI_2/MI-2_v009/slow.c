void slow_mi2_v009(double *out,double *A,double *B,int n){
    memset(out,0,n*sizeof(double));
    for(int i=0;i<n;i++) out[i]=A[i]*(double)2.0+B[i]*(double)0.5;
}