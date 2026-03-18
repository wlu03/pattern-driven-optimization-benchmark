#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_mi2_v022(double *output, double *A, double *B, int n) {
    memset(output, 0, n * sizeof(double));
    for (int i = 0; i < n; i++) output[i] = A[i] + B[i];
}