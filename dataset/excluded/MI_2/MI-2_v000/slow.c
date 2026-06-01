#include <stdlib.h>
void mi2_zero_v000(void *p, int n);

void slow_mi2_v000(float *out,float *A,float *B,int n){
    float *s1=(float*)malloc(n*sizeof(float));
    float *s2=(float*)malloc(n*sizeof(float));
    mi2_zero_v000(s1, n*(int)sizeof(float));
    for(int i=0;i<n;i++) s1[i]=A[i]+B[i];
    mi2_zero_v000(s2, n*(int)sizeof(float));
    for(int i=0;i<n;i++) s2[i]=s1[i];
    mi2_zero_v000(out, n*(int)sizeof(float));
    for(int i=0;i<n;i++) out[i]=s2[i];
    free(s1); free(s2);
}
