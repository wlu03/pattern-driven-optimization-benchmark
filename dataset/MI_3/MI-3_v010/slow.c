#include <stdlib.h>
void* mi3_alloc_v010(int n);
void mi3_free_v010(void *p);

double slow_mi3_v010(double *data,int n){
    double total=0.0;
    for(int i=0;i<n-7;i++){
        double *buf=(double*)mi3_alloc_v010(8*(int)sizeof(double));
        buf[0]=data[i+0]; buf[1]=data[i+1]; buf[2]=data[i+2]; buf[3]=data[i+3]; buf[4]=data[i+4]; buf[5]=data[i+5]; buf[6]=data[i+6]; buf[7]=data[i+7];
        double sum=0.0; for(int j=0;j<8;j++) sum+=buf[j];
        total+=sum*0.125;
        mi3_free_v010(buf);
    }
    return total;
}