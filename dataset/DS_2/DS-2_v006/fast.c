#include <stdlib.h>
void fast_ds2_v006(double *results,double *input,int n,int chunk){
    double *tmp=(double*)malloc(chunk*sizeof(double));
    for(int i=0;i<n;i+=chunk){
        int sz=(i+chunk<=n)?chunk:(n-i);
        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];
        double sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];
        results[i/chunk]=sum;
    }
    free(tmp);
}
