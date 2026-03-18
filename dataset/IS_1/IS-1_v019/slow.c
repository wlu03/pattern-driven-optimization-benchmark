#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float is1_kernel_v019(float a, float b);
void slow_is1_v019(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) out[i] = is1_kernel_v019(A[i], B[i]);
}