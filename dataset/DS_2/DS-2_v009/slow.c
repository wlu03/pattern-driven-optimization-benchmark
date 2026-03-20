#include <stdlib.h>
void* ds2_alloc_v009(int n);
void ds2_free_v009(void *p);

void slow_ds2_v009(float *results,float *input,int n,int chunk){
    for(int i=0;i<n;i+=chunk){
        int sz=(i+chunk<=n)?chunk:(n-i);
        float *tmp=(float*)ds2_alloc_v009(sz*(int)sizeof(float));
        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];
        float sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];
        results[i/chunk]=sum;
        ds2_free_v009(tmp);
    }
}
