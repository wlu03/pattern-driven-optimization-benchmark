void fast_mi2_v008(double *out,double *A,double *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*(double)2.0+B[i]*(double)0.5;
}
