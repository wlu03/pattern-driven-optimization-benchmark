int slow_is3_v008(float *arr,int n,float thr){
    int cnt=0;
    for(int i=0;i<n;i++) if(arr[i]>thr) cnt++;
    return cnt==0;
}