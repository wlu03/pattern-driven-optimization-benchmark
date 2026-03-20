double fast_hr4_v002(double *arr,int n){
    double sum=0;
    for(int i=0;i<n;i++) sum+=arr[i]*(double)2.0+(double)1.0;
    return sum;
}