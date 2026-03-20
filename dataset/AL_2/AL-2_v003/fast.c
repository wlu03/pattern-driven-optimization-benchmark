void fast_al2_v003(float *arr,int *sz,float *items,int n){
    *sz=0;
    for(int i=0;i<n;i++){
        float val=items[i];
        int lo=0,hi=*sz;
        while(lo<hi){int mid=(lo+hi)/2;if(arr[mid]<val) lo=mid+1;else hi=mid;}
        memmove(&arr[lo+1],&arr[lo],(*sz-lo)*sizeof(float));
        arr[lo]=val;
        (*sz)++;
    }
}