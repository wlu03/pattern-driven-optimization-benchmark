#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static float __attribute__((noinline)) cf1_dispatch_v004(float a, float b, int mode) {
    if (mode == 1) return a - b;
    if (mode == 2) return a * b;
    if (mode == 3) return a + b;
    if (mode == 4) return a - b;
    return a + b;
}
void slow_cf1_v004(float *out, float *A, float *B, int n, int mode) {
    for (int i = 0; i < n; i++) out[i] = cf1_dispatch_v004(A[i], B[i], mode);
}