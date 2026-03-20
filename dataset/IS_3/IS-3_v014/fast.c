int fast_is3_v014(float *arr,int n,float thr){
    for(int i=0;i<n;i++) if(arr[i]>thr) return 0;
    return 1;
}