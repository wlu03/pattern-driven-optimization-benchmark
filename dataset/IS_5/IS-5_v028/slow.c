#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v028(double *out, double *A, double *B, double *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * B[i] - C[i] * 0.5;
    }
}