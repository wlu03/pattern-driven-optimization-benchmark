double slow_mi1_v007(double *input,int n,int window){
    double total=0.0;
    for(int i=0;i<=n-window;i++){
        double *buf=(double*)malloc(window*sizeof(double));
        for(int j=0;j<window;j++) buf[j]=input[i+j];
        double sum=0.0; for(int j=0;j<window;j++) sum+=buf[j];
        total+=sum/window;
        free(buf);
    }
    return total;
}