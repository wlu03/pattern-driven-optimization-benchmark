#include <stdlib.h>
__attribute__((noinline))
void slow_is5_v009(double *out, double *A, double *B, int n) {
    double *tmp1 = (double *)malloc(n * sizeof(double));
    double *tmp2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) tmp1[i] = A[i] - B[i];
    for (int i = 0; i < n; i++) tmp2[i] = tmp1[i] * 2.0 + B[i];
    for (int i = 0; i < n; i++) out[i] = tmp2[i] * tmp2[i] - A[i];
    free(tmp1); free(tmp2);
}