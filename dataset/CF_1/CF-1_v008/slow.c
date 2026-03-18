#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf1_dispatch_v008(int a, int b, int c, int mode) {
    if (mode == 1) return (a - b) - c;
    return (a * b) - c;
}
void slow_cf1_v008(int *out, int *A, int *B, int *C, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v008(A[i], B[i], C[i], mode);
}