void fast_mi2_v009(double *out,double *A,double *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*B[i]+(double)1.0;
}
