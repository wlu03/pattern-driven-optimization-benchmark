void fast_ds2_v012(float *results,float *input,int n,int chunk){
    float *tmp=(float*)malloc(chunk*sizeof(float));
    for(int i=0;i<n;i+=chunk){
        int sz=(i+chunk<=n)?chunk:(n-i);
        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];
        float sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];
        results[i/chunk]=sum;
    }
    free(tmp);
}