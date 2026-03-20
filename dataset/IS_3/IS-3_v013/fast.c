int fast_is3_v013(double *arr,int n,double thr){
    for(int i=0;i<n;i++) if(arr[i]>thr) return 0;
    return 1;
}