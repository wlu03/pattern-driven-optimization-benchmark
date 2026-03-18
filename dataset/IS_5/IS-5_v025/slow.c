#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v025(float *out, float *A, float *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = A[i] * B[i] + A[i] + B[i];
        i++;
    }
}