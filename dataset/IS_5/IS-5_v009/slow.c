#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v009(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = A[i] * A[i] - A[i] * 0.5 + B[i] * B[i] + B[i];
        i++;
    }
}