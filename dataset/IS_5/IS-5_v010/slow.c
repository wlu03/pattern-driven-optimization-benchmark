#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v010(float *out, float *A, float *B, float *C, int n) {
    int i = 0;
    while (i < n) {
        out[i] = 0.5f * A[i] + 0.3f * B[i] + 0.2f * C[i];
        i++;
    }
}