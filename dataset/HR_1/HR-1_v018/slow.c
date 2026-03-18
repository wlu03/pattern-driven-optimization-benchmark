#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v018(float *out, float *A, float *B, float *C, float *D, int n) {
    int i = 0;
    while (i < n) {
        float temp1 = A[i] + B[i];
        float temp2 = temp1 + C[i];
        float temp3 = temp2 + A[i];
        float result = temp3;
        out[i] = result;
        i++;
    }
}