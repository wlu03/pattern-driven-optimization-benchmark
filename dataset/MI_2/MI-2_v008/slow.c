#include <stdlib.h>
void mi2_zero_v008(void *p, int n);

void slow_mi2_v008(double *out,double *A,double *B,int n){
    double *s1=(double*)malloc(n*sizeof(double));
    double *s2=(double*)malloc(n*sizeof(double));
    mi2_zero_v008(s1, n*(int)sizeof(double));
    for(int i=0;i<n;i++) s1[i]=A[i]*(double)2.0+B[i]*(double)0.5;
    mi2_zero_v008(s2, n*(int)sizeof(double));
    for(int i=0;i<n;i++) s2[i]=s1[i];
    mi2_zero_v008(out, n*(int)sizeof(double));
    for(int i=0;i<n;i++) out[i]=s2[i];
    free(s1); free(s2);
}
