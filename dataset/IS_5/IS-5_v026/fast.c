#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is5_v026(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        double t1 = A[i] - B[i];
        double t2 = t1 * 3.0 + B[i];
        out[i] = t2 * t2 - A[i];
    }
}