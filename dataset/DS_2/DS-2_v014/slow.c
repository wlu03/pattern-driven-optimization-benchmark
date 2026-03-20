#include <stdlib.h>
void* ds2_alloc_v014(int n);
void ds2_free_v014(void *p);

void slow_ds2_v014(double *results,double *input,int n,int chunk){
    for(int i=0;i<n;i+=chunk){
        int sz=(i+chunk<=n)?chunk:(n-i);
        double *tmp=(double*)ds2_alloc_v014(sz*(int)sizeof(double));
        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];
        double sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];
        results[i/chunk]=sum;
        ds2_free_v014(tmp);
    }
}
