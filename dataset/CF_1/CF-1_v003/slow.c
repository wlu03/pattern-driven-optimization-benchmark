#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf1_dispatch_v003(int a, int b, int mode) {
    if (mode == 1) return a * b;
    return a + b;
}
void slow_cf1_v003(int *out, int *A, int *B, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v003(A[i], B[i], mode);
}