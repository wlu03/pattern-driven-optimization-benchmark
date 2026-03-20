#include <stdlib.h>
void mi2_zero_v001(void *p, int n);

void slow_mi2_v001(double *out,double *A,double *B,int n){
    double *s1=(double*)malloc(n*sizeof(double));
    double *s2=(double*)malloc(n*sizeof(double));
    mi2_zero_v001(s1, n*(int)sizeof(double));
    for(int i=0;i<n;i++) s1[i]=A[i]+B[i];
    mi2_zero_v001(s2, n*(int)sizeof(double));
    for(int i=0;i<n;i++) s2[i]=s1[i];
    mi2_zero_v001(out, n*(int)sizeof(double));
    for(int i=0;i<n;i++) out[i]=s2[i];
    free(s1); free(s2);
}
