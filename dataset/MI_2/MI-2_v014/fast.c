void fast_mi2_v014(float *out,float *A,float *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*B[i]+(float)1.0f;
}
