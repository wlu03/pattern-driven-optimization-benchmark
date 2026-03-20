#include <stdlib.h>
void* mi3_alloc_v008(int n);
void mi3_free_v008(void *p);

double slow_mi3_v008(double *data,int n){
    double total=0.0;
    for(int i=0;i<n-3;i++){
        double *buf=(double*)mi3_alloc_v008(4*(int)sizeof(double));
        buf[0]=data[i+0]; buf[1]=data[i+1]; buf[2]=data[i+2]; buf[3]=data[i+3];
        double sum=0.0; for(int j=0;j<4;j++) sum+=buf[j];
        total+=sum*0.125;
        mi3_free_v008(buf);
    }
    return total;
}