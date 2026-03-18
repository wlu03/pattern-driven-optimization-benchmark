#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double is1_kernel_v020(double a, double b);
void slow_is1_v020(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) out[i] = is1_kernel_v020(A[i], B[i]);
}