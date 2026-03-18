#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v012(double *out, double *A, double *B, double *C, int n) {
    int i = 0;
    while (i < n) {
        out[i] = A[i] * A[i] + B[i] * B[i] - C[i] * 0.5;
        i++;
    }
}