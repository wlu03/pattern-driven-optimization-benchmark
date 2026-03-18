#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf1_dispatch_v029(int a, int b, int c, int mode) {
    if (mode == 1) return (a - b) - c;
    if (mode == 2) return (a + b) - c;
    return (a * b) + c;
}
void slow_cf1_v029(int *out, int *A, int *B, int *C, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v029(A[i], B[i], C[i], mode);
}