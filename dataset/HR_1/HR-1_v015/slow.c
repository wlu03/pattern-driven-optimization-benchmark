#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v015(float *out, float *A, float *B, float *C, int n) {
    for (int i = 0; i < n; i++) {
        float temp1 = A[i] * B[i];
        float temp2 = temp1 * A[i];
        float result = temp2;
        out[i] = result;
    }
}