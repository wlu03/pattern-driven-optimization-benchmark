void slow_ds2_v003(float *results,float *input,int n,int chunk){
    for(int i=0;i<n;i+=chunk){
        int sz=(i+chunk<=n)?chunk:(n-i);
        float *tmp=(float*)malloc(sz*sizeof(float));
        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];
        float sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];
        results[i/chunk]=sum;
        free(tmp);
    }
}