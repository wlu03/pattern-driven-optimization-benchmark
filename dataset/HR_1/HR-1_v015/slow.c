#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v015(float *out, float *A, float *B, float *C, float *D, int n) {
    for (int i = 0; i < n; i++) {
        float temp1 = A[i] - B[i];
        float temp2 = temp1 + C[i];
        float temp3 = temp2 * D[i];
        float temp4 = temp3 + A[i];
        float temp5 = temp4 + B[i];
        float temp6 = temp5 * A[i];
        float result = temp6;
        out[i] = result;
    }
}