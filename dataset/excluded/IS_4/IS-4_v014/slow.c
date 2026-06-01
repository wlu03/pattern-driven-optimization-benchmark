static int cmp_is4_v014(const void *a,const void *b){return (*(int*)a-*(int*)b);}

void slow_is4_v014(int *arr,int n){
    qsort(arr,n,sizeof(int),cmp_is4_v014);
}