#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v009(float *out, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) {
        float temp1 = A[i] * B[i];
        float temp2 = temp1 - A[i];
        float temp3 = temp2 + B[i];
        float temp4 = temp3 * A[i];
        float temp5 = temp4 * A[i];
        float result = temp5;
        out[i] = result;
    }
}