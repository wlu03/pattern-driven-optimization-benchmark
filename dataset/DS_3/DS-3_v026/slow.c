#include <stdlib.h>
__attribute__((noinline))
void slow_ds3_v026(double *out, double *A, double *B, int n) {
    double *t1 = (double *)malloc(n * sizeof(double));
    double *t2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) t1[i] = A[i] - B[i];
    for (int i = 0; i < n; i++) t2[i] = t1[i] * 2.0 + B[i];
    for (int i = 0; i < n; i++) out[i] = t2[i] * A[i];
    free(t1); free(t2);
}