static int cmp_al2_v000(const void *a,const void *b){
    float da=*(float*)a,db=*(float*)b;
    return (da>db)-(da<db);
}

void slow_al2_v000(float *arr,int *sz,float *items,int n){
    *sz=0;
    for(int i=0;i<n;i++){
        arr[(*sz)++]=items[i];
        qsort(arr,*sz,sizeof(float),cmp_al2_v000);
    }
}