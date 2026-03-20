static int cmp_is4_v005(const void *a,const void *b){return (*(int*)a-*(int*)b);}

void fast_is4_v005(int *arr,int n){
    int inv=0; unsigned seed=12345u;
    for(int s=0;s<64;s++){
        seed=seed*1664525u+1013904223u;
        int i=(int)((seed>>1)%(unsigned)(n-1));
        if(arr[i]>arr[i+1]) inv++;
    }
    if(inv<=2){
        for(int i=1;i<n;i++){
            int key=arr[i],j=i-1;
            while(j>=0&&arr[j]>key){arr[j+1]=arr[j];j--;}
            arr[j+1]=key;
        }
    }else{
        qsort(arr,n,sizeof(int),cmp_is4_v005);
    }
}