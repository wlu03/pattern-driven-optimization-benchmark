#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float is1_kernel_v017(float a, float b);
void slow_is1_v017(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) out[i] = is1_kernel_v017(A[i], B[i]);
}