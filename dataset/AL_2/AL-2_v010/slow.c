static int cmp_al2_v010(const void *a,const void *b){
    double da=*(double*)a,db=*(double*)b;
    return (da>db)-(da<db);
}

void slow_al2_v010(double *arr,int *sz,double *items,int n){
    *sz=0;
    for(int i=0;i<n;i++){
        arr[(*sz)++]=items[i];
        qsort(arr,*sz,sizeof(double),cmp_al2_v010);
    }
}