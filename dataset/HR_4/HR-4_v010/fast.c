float fast_hr4_v010(float *A,float *B,int n){
    float sum=0;
    for(int i=0;i<n;i++){sum+=A[i]*B[i];}
    return sum;
}