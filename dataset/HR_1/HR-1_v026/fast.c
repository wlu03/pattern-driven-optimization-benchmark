#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v026(float *out, float *A, float *B, float *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = (((((A[i] + B[i]) + C[i]) * A[i]) - B[i]) * C[i]) - A[i];
    }
}