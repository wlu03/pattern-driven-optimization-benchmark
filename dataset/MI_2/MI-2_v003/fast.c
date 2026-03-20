void fast_mi2_v003(float *out,float *A,float *B,int n){
    for(int i=0;i<n;i++) out[i]=A[i]*(float)2.0f+B[i]*(float)0.5f;
}