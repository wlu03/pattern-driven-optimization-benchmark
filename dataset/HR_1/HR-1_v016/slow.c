#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v016(float *out, float *A, float *B, float *C, int n) {
    int i = 0;
    while (i < n) {
        float temp1 = A[i] * B[i];
        float temp2 = temp1 * A[i];
        float result = temp2;
        out[i] = result;
        i++;
    }
}