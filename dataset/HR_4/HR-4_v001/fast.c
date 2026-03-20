float fast_hr4_v001(float *arr,int n){
    float sum=0;
    for(int i=0;i<n;i++){sum+=arr[i]*(float)2.0f+(float)1.0f;}
    return sum;
}