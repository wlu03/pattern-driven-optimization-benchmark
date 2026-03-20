#include <stdlib.h>
void* mi3_alloc_v003(int n);
void mi3_free_v003(void *p);

double slow_mi3_v003(double *data,int n){
    double total=0.0;
    for(int i=0;i<n-3;i++){
        double *buf=(double*)mi3_alloc_v003(4*(int)sizeof(double));
        buf[0]=data[i+0]; buf[1]=data[i+1]; buf[2]=data[i+2]; buf[3]=data[i+3];
        double sum=0.0; for(int j=0;j<4;j++) sum+=buf[j];
        total+=sum*0.5;
        mi3_free_v003(buf);
    }
    return total;
}