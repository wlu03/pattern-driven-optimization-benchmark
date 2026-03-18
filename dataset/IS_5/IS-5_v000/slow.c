#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v000(float *out, float *A, float *B, float *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] + B[i] + C[i];
    }
}