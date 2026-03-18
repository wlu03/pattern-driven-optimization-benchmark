#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double __attribute__((noinline)) cf1_dispatch_v004(double a, double b, int mode) {
    if (mode == 1) return a * b;
    if (mode == 2) return a - b;
    if (mode == 3) return a + b;
    return a + b;
}
void slow_cf1_v004(double *out, double *A, double *B, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v004(A[i], B[i], mode);
}