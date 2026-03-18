#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v010(float *out, float *A, float *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] += A[i] * 2.0f + B[i] * 0.5f;
        i++;
    }
}