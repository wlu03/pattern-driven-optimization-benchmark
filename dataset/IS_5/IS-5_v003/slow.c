#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v003(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = A[i] * A[i] + B[i] * 2.0;
        i++;
    }
}