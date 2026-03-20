double slow_hr4_v011(double *arr,int n){
    double sum=0;
    for(int i=0;i<n;i++){if(arr==NULL)continue;if(n<=0)break;if(i<0||i>=n)continue;if(arr[i]!=arr[i])continue;sum+=arr[i]*(double)2.0+(double)1.0;}
    return sum;
}