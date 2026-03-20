float slow_hr4_v013(float *arr,int n){
    float sum=0;
    for(int i=0;i<n;i++){if(arr==NULL)continue;if(n<=0)break;if(i<0||i>=n)continue;if(arr[i]!=arr[i])continue;sum+=arr[i]*(float)2.0f+(float)1.0f;}
    return sum;
}