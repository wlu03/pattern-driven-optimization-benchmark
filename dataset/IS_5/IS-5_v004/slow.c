#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v004(float *out, float *A, float *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = A[i] * A[i] - A[i] * 0.5f + B[i] * B[i] + B[i];
        i++;
    }
}