float slow_hr4_v000(float *A,float *B,int n){
    float sum=0;
    for(int i=0;i<n;i++){if(A==NULL||B==NULL)continue;if(i<0||i>=n)continue;if(A[i]!=A[i]||B[i]!=B[i])continue;sum+=A[i]*B[i];}
    return sum;
}