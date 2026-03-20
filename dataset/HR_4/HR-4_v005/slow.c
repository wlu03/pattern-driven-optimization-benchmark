float hr4_check_v005(float *A, float *B, int idx, int n);

float slow_hr4_v005(float *A,float *B,int n){
    float sum=0;
    for(int i=0;i<n;i++) sum+=hr4_check_v005(A,B,i,n);
    return sum;
}