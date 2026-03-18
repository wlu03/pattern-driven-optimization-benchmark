#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double is1_kernel_v011(double a, double b);
void fast_is1_v011(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        if (A[i] == (double)0.0) { out[i] = 0.0; }
        else out[i] = is1_kernel_v011(A[i], B[i]);
    }
}