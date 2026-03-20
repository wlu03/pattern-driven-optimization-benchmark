float hr4_check_v003(float *arr, int idx, int n);

float slow_hr4_v003(float *arr,int n){
    float sum=0;
    for(int i=0;i<n;i++) sum+=hr4_check_v003(arr,i,n);
    return sum;
}