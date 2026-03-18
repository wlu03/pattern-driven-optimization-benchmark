#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_mi2_v011(float *output, float *A, float *B, int n) {
    for (int i = 0; i < n; i++) output[i] = A[i] * A[i] + B[i];
}