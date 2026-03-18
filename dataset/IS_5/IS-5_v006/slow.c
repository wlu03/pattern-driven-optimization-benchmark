#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v006(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * 2.0f;
    }
}