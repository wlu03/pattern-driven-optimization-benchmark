#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is5_v019(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] += A[i] * 2.0 + B[i] * 0.5;
        i++;
    }
}