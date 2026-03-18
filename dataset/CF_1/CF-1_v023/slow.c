#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double __attribute__((noinline)) cf1_dispatch_v023(double a, double b, double c, int mode) {
    if (mode == 1) return (a - b) - c;
    return (a + b) + c;
}
void slow_cf1_v023(double *out, double *A, double *B, double *C, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v023(A[i], B[i], C[i], mode);
}