double hr4_check_v003(double *arr, int idx, int n);

double slow_hr4_v003(double *arr,int n){
    double sum=0;
    for(int i=0;i<n;i++) sum+=hr4_check_v003(arr,i,n);
    return sum;
}